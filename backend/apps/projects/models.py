"""
Projects & Tasks models.
TZ §6.6 — паспорт проекта, задачи, фазы, зависимости.

Tables: projects, project_roles, project_requirements, required_skills
        (requirement_skills), tasks, task_dependencies
"""
import uuid
from django.db import models
from apps.authentication.models import User
from apps.organization.models import Employee, Skill


# ═══════════════════════════════════════════════════════════════════
#  Enums (TZ §6.6)
# ═══════════════════════════════════════════════════════════════════

class ProjectStatus(models.TextChoices):
    """Полный набор статусов проекта согласно ТЗ §6.6."""
    IDEA        = 'IDEA',        'Идея'
    PLANNING    = 'PLANNING',    'Планирование'
    ACTIVE      = 'ACTIVE',      'Активный'
    PAUSED      = 'PAUSED',      'На паузе'
    COMPLETED   = 'COMPLETED',   'Завершён'
    CANCELLED   = 'CANCELLED',   'Отменён'


class ProjectPriority(models.TextChoices):
    CRITICAL = 'CRITICAL', 'Критический'
    HIGH     = 'HIGH',     'Высокий'
    MEDIUM   = 'MEDIUM',   'Средний'
    LOW      = 'LOW',      'Низкий'


class ProjectType(models.TextChoices):
    DEVELOPMENT  = 'DEVELOPMENT',  'Разработка'
    CONSULTING   = 'CONSULTING',   'Консалтинг'
    RESEARCH     = 'RESEARCH',     'Исследование'
    SUPPORT      = 'SUPPORT',      'Поддержка'


class ProjectPhase(models.TextChoices):
    """Фазы жизненного цикла проекта (ТЗ §6.6)."""
    INITIATION   = 'INITIATION',   'Инициация'
    PLANNING     = 'PLANNING',     'Планирование'
    EXECUTION    = 'EXECUTION',    'Исполнение'
    MONITORING   = 'MONITORING',   'Мониторинг'
    CLOSING      = 'CLOSING',      'Завершение'


class TaskType(models.TextChoices):
    DEVELOPMENT   = 'DEVELOPMENT',   'Разработка'
    DESIGN        = 'DESIGN',        'Дизайн'
    TESTING       = 'TESTING',       'Тестирование'
    DOCUMENTATION = 'DOCUMENTATION', 'Документация'
    MEETING       = 'MEETING',       'Встреча'


class TaskStatus(models.TextChoices):
    BACKLOG     = 'BACKLOG',     'Бэклог'
    TODO        = 'TODO',        'К выполнению'
    IN_PROGRESS = 'IN_PROGRESS', 'В работе'
    REVIEW      = 'REVIEW',      'На проверке'
    DONE        = 'DONE',        'Завершено'
    BLOCKED     = 'BLOCKED',     'Заблокировано'


class ProjectRoleSlot(models.TextChoices):
    """Квоты участников по ролям (ТЗ §6.6)."""
    PM         = 'PM',         'Project Manager'
    TEAM_LEAD  = 'TEAM_LEAD',  'Team Lead'
    DEVELOPER  = 'DEVELOPER',  'Developer'
    DESIGNER   = 'DESIGNER',   'Designer'
    ANALYST    = 'ANALYST',    'Analyst'
    QA         = 'QA',         'QA Engineer'
    DEVOPS     = 'DEVOPS',     'DevOps'
    CONSULTANT = 'CONSULTANT', 'Consultant'
    CUSTOM     = 'CUSTOM',     'Пользовательская роль'


# ═══════════════════════════════════════════════════════════════════
#  Models
# ═══════════════════════════════════════════════════════════════════

class Project(models.Model):
    """
    Таблица `projects` — паспорт проекта (ТЗ §6.6).
    Все обязательные поля + фазы, бюджет, зависимости.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200)
    code        = models.CharField(max_length=50, unique=True,
                                   help_text='Уникальный код проекта')
    description = models.TextField(blank=True)
    client      = models.CharField(max_length=200, blank=True)
    is_external_client = models.BooleanField(default=False)

    # Статус и приоритет
    status   = models.CharField(max_length=20, choices=ProjectStatus.choices,
                                default=ProjectStatus.PLANNING)
    priority = models.CharField(max_length=20, choices=ProjectPriority.choices,
                                default=ProjectPriority.MEDIUM)
    proj_type = models.CharField(max_length=20, choices=ProjectType.choices,
                                 default=ProjectType.DEVELOPMENT)
    phase     = models.CharField(max_length=20, choices=ProjectPhase.choices,
                                 default=ProjectPhase.INITIATION)

    # Даты
    planned_start = models.DateField()
    planned_end   = models.DateField()
    actual_start  = models.DateField(null=True, blank=True)
    actual_end    = models.DateField(null=True, blank=True)

    # Бюджет
    budget_hours  = models.PositiveIntegerField(default=0)
    budget_money  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency      = models.CharField(max_length=3, default='RUB')

    # Рабочие параметры
    timezone      = models.CharField(max_length=60, default='Europe/Moscow')
    work_format   = models.CharField(max_length=20, default='OFFICE')
    has_mandatory_meetings = models.BooleanField(default=True)

    # Зависимости между проектами
    depends_on    = models.ManyToManyField('self', symmetrical=False, blank=True,
                                           related_name='blocking')

    # Ответственный PM
    project_manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='managed_projects')

    # Audit (ТЗ §8.1)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_projects')
    updated_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='updated_projects')
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'projects'
        indexes  = [
            # TZ §8.3 — составной индекс по статусу и датам
            models.Index(fields=['status', 'planned_start', 'planned_end'],
                         name='projects_status_dates_idx'),
        ]
        ordering = ['-planned_start']

    def __str__(self):
        return f'[{self.code}] {self.name}'


class ProjectRoleRequirement(models.Model):
    """
    Таблица `project_roles` / `project_requirements`.
    TZ §6.6 — квоты участников по ролям с требуемыми навыками.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project      = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requirements')
    role_slot    = models.CharField(max_length=20, choices=ProjectRoleSlot.choices)
    role_name    = models.CharField(max_length=100, blank=True,
                                    help_text='Для CUSTOM роли')
    headcount    = models.PositiveSmallIntegerField(default=1,
                                                    help_text='Количество позиций')
    min_grade    = models.CharField(max_length=20, default='MIDDLE')
    hours_per_week = models.PositiveSmallIntegerField(default=40)
    is_mandatory   = models.BooleanField(default=True)

    class Meta:
        db_table = 'project_requirements'


class RequiredSkill(models.Model):
    """
    Таблица `required_skills` (requirement_skills).
    TZ §6.6 — навыки с минимальными уровнями для требования.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement = models.ForeignKey(ProjectRoleRequirement, on_delete=models.CASCADE,
                                    related_name='required_skills')
    skill       = models.ForeignKey(Skill, on_delete=models.CASCADE)
    min_level   = models.PositiveSmallIntegerField(default=3,
                                                   help_text='Минимальный требуемый уровень (1–5)')
    is_mandatory = models.BooleanField(default=True,
                                       help_text='True = жёсткое ограничение алгоритма')

    class Meta:
        db_table = 'required_skills'
        unique_together = ('requirement', 'skill')


class Task(models.Model):
    """
    Таблица `tasks` — задачи проекта (ТЗ §6.6).
    Kanban, Gantt, назначение исполнителей.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type   = models.CharField(max_length=20, choices=TaskType.choices,
                                   default=TaskType.DEVELOPMENT)
    priority    = models.CharField(max_length=20, choices=ProjectPriority.choices,
                                   default=ProjectPriority.MEDIUM)
    status      = models.CharField(max_length=20, choices=TaskStatus.choices,
                                   default=TaskStatus.BACKLOG)

    # Исполнители
    assignee    = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_tasks')
    role_slot   = models.CharField(max_length=20, choices=ProjectRoleSlot.choices, blank=True)

    # Даты и трудоёмкость
    planned_start   = models.DateField(null=True, blank=True)
    planned_end     = models.DateField(null=True, blank=True)
    actual_start    = models.DateField(null=True, blank=True)
    actual_end      = models.DateField(null=True, blank=True)
    estimated_hours = models.PositiveIntegerField(default=0)
    logged_hours    = models.PositiveIntegerField(default=0)
    progress_percent = models.PositiveSmallIntegerField(default=0)

    # Вложенность (Kanban/Gantt)
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='subtasks')

    # Навыки для задачи
    required_skills = models.ManyToManyField(Skill, blank=True, related_name='tasks')

    # Audit
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_tasks')
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['planned_start', 'priority']


class TaskDependency(models.Model):
    """Таблица `task_dependencies` — зависимости между задачами."""
    class DependencyType(models.TextChoices):
        FINISH_TO_START  = 'FS', 'Конец → Начало (FS)'
        START_TO_START   = 'SS', 'Начало → Начало (SS)'
        FINISH_TO_FINISH = 'FF', 'Конец → Конец (FF)'

    task       = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='blocking_tasks')
    dep_type   = models.CharField(max_length=2, choices=DependencyType.choices,
                                  default=DependencyType.FINISH_TO_START)

    class Meta:
        db_table = 'task_dependencies'
        unique_together = ('task', 'depends_on')
