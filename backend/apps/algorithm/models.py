"""
Algorithm & Teams models.
TZ §6.8 — алгоритм формирования команд (жадный + генетический).

Tables: team_runs (matching_runs), team_variants (matching_results),
        matching_scores, teams, team_members, team_conflicts
"""
import uuid
from django.db import models
from apps.authentication.models import User
from apps.organization.models import Employee
from apps.projects.models import Project, ProjectRoleRequirement


class MatchingRunStatus(models.TextChoices):
    PENDING   = 'PENDING',   'В очереди'
    RUNNING   = 'RUNNING',   'Выполняется'
    COMPLETED = 'COMPLETED', 'Завершён'
    FAILED    = 'FAILED',    'Ошибка'


class TeamRun(models.Model):
    """
    Таблица `team_runs` (matching_runs).
    TZ §6.8 — один запуск алгоритма формирования команды.
    Результаты — 3–5 вариантов (team_variants).
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_runs')
    status     = models.CharField(max_length=20, choices=MatchingRunStatus.choices,
                                  default=MatchingRunStatus.PENDING)

    # Параметры расчёта
    weights    = models.JSONField(default=dict,
                                  help_text='Веса K/A/L/T/C, если задан нестандартный набор')
    # Параметры запуска
    algorithm  = models.CharField(max_length=20, default='GREEDY',
                                  help_text='GREEDY | GENETIC | HYBRID')
    max_variants = models.PositiveSmallIntegerField(default=5,
                                                    help_text='Количество вариантов (3–5)')
    celery_task_id = models.CharField(max_length=255, blank=True)

    # Результат
    variants_count = models.PositiveSmallIntegerField(default=0)
    duration_ms    = models.PositiveIntegerField(default=0)
    error_message  = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='team_runs')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'team_runs'
        ordering = ['-created_at']

    def __str__(self):
        return f'TeamRun[{self.project}] #{self.id}'


class TeamVariant(models.Model):
    """
    Таблица `team_variants` (matching_results).
    TZ §6.8 — один вариант состава команды (от 1 до 5).
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run         = models.ForeignKey(TeamRun, on_delete=models.CASCADE, related_name='variants')
    variant_num = models.PositiveSmallIntegerField(help_text='Номер варианта 1–5')

    # Итоговые метрики варианта
    total_score          = models.FloatField(default=0.0)
    skill_coverage_pct   = models.FloatField(default=0.0,
                                             help_text='Покрытие обязательных навыков (%)')
    avg_availability_pct = models.FloatField(default=0.0)
    avg_load_pct         = models.FloatField(default=0.0)
    risk_level           = models.CharField(max_length=20, default='LOW',
                                            help_text='LOW | MEDIUM | HIGH')

    # Объяснение выбора (для прозрачности §1.3)
    explanation          = models.TextField(blank=True)

    # Статус: черновик → утверждён
    is_approved          = models.BooleanField(default=False)
    approved_by          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='approved_variants')
    approved_at          = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at  = models.DateTimeField(auto_now_add=True)
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'team_variants'
        unique_together = ('run', 'variant_num')
        ordering = ['-total_score']


class MatchingScore(models.Model):
    """
    Таблица `matching_scores`.
    TZ §6.8 — детальные оценки каждого кандидата в варианте.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant     = models.ForeignKey(TeamVariant, on_delete=models.CASCADE, related_name='scores')
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='matching_scores')
    requirement = models.ForeignKey(ProjectRoleRequirement, on_delete=models.SET_NULL,
                                    null=True, related_name='matching_scores')

    # Компоненты формулы S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C
    k_score     = models.FloatField(help_text='Навыки (K), вес 35%')
    a_score     = models.FloatField(help_text='Доступность (A), вес 25%')
    l_score     = models.FloatField(help_text='Баланс нагрузки (L), вес 20%')
    t_score     = models.FloatField(help_text='Совместимость расписаний (T), вес 10%')
    c_score     = models.FloatField(help_text='Совместимость с коллегами (C), вес 10%')
    total_score = models.FloatField(help_text='Итоговый балл S')

    # Пояснения
    k_detail    = models.JSONField(default=dict, blank=True)   # {skill: level_emp vs level_req}
    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'matching_scores'
        unique_together = ('variant', 'employee')


class Team(models.Model):
    """
    Таблица `teams` — утверждённый состав команды проекта.
    Создаётся при утверждении одного из вариантов TeamVariant.
    """
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project  = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='team')
    variant  = models.ForeignKey(TeamVariant, on_delete=models.SET_NULL, null=True, blank=True)
    name     = models.CharField(max_length=200, blank=True)
    formed_at = models.DateTimeField(auto_now_add=True)
    formed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'teams'

    def __str__(self):
        return f'Team for [{self.project.code}]'


class TeamMember(models.Model):
    """Таблица `team_members` — участники утверждённой команды."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team       = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='team_memberships')
    requirement= models.ForeignKey(ProjectRoleRequirement, on_delete=models.SET_NULL, null=True)
    role_slot  = models.CharField(max_length=20, blank=True)
    is_lead    = models.BooleanField(default=False)

    # Параметры назначения
    allocated_hours_per_week = models.PositiveSmallIntegerField(default=40)
    join_date  = models.DateField(null=True, blank=True)
    leave_date = models.DateField(null=True, blank=True)

    final_score = models.FloatField(default=0.0)

    # Audit
    added_at   = models.DateTimeField(auto_now_add=True)
    added_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'team_members'
        unique_together = ('team', 'employee')


class TeamConflict(models.Model):
    """
    Таблица `team_conflicts` — обнаруженные конфликты ресурсов.
    (Например, один сотрудник назначен на 2 критических проекта одновременно.)
    """
    class ConflictType(models.TextChoices):
        OVERLOAD       = 'OVERLOAD',       'Перегрузка сотрудника'
        ABSENCE_OVERLAP= 'ABSENCE_OVERLAP','Пересечение с отсутствием'
        DOUBLE_BOOKING = 'DOUBLE_BOOKING', 'Двойное бронирование'
        SKILL_GAP      = 'SKILL_GAP',      'Нехватка навыков'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_member  = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='conflicts')
    conflict_type = models.CharField(max_length=30, choices=ConflictType.choices)
    description  = models.TextField()
    severity     = models.CharField(max_length=10, default='MEDIUM')
    is_resolved  = models.BooleanField(default=False)
    resolved_at  = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team_conflicts'
