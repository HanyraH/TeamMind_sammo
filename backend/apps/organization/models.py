"""
Organization & Employee models.
TZ §6.2, §6.4, §6.5 — сотрудники, отделы, должности, навыки, предпочтения.

Tables:
  departments, department_managers, positions, grades,
  employees, employee_departments, employee_contacts, employee_settings,
  skill_categories, skills, employee_skills, skill_evaluations,
  certifications, languages, employee_languages,
  chronotypes, work_formats, work_preferences (employee_preferences),
  compatibility_preferences (colleague_preferences),
  work_schedules, schedule_exceptions
"""
import uuid
from django.db import models
from apps.authentication.models import User


# ═══════════════════════════════════════════════════════════════════
#  SECTION 1 — Organizational structure
# ═══════════════════════════════════════════════════════════════════

class Department(models.Model):
    """Таблица `departments`."""
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=150)
    code        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    parent      = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subdepartments'
    )
    # Audit fields (обязательные по ТЗ §8.1)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return self.name


class DepartmentManager(models.Model):
    """Таблица `department_managers` — связь отдел↔руководитель."""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='managers')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_departments')
    is_primary = models.BooleanField(default=True)

    class Meta:
        db_table = 'department_managers'
        unique_together = ('department', 'user')


class Grade(models.TextChoices):
    """Грейды ТЗ §6.2."""
    INTERN    = 'INTERN',    'Intern'
    JUNIOR    = 'JUNIOR',    'Junior'
    MIDDLE    = 'MIDDLE',    'Middle'
    SENIOR    = 'SENIOR',    'Senior'
    LEAD      = 'LEAD',      'Lead'
    PRINCIPAL = 'PRINCIPAL', 'Principal'


class Position(models.Model):
    """Таблица `positions`."""
    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    grade = models.CharField(max_length=20, choices=Grade.choices, default=Grade.MIDDLE)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'positions'

    def __str__(self):
        return f'{self.title} ({self.grade})'


# ═══════════════════════════════════════════════════════════════════
#  SECTION 2 — Employee profile (TZ §6.2)
# ═══════════════════════════════════════════════════════════════════

class EmployeeStatus(models.TextChoices):
    ACTIVE    = 'ACTIVE',    'Активен'
    ON_LEAVE  = 'ON_LEAVE',  'В отпуске'
    FIRED     = 'FIRED',     'Уволен'
    MATERNITY = 'MATERNITY', 'Декрет'
    REMOTE    = 'REMOTE',    'Удалённо'


class WorkFormat(models.TextChoices):
    OFFICE  = 'OFFICE',  'Офис'
    REMOTE  = 'REMOTE',  'Удалённо'
    HYBRID  = 'HYBRID',  'Гибрид'
    FLEXIBLE= 'FLEXIBLE','Гибкий'


class Chronotype(models.TextChoices):
    """ТЗ §6.4 — 4 хронотипа."""
    LARK         = 'LARK',         'Жаворонок (06:00–12:00)'
    OWL          = 'OWL',          'Сова (18:00–00:00)'
    INTERMEDIATE = 'INTERMEDIATE', 'Промежуточный (10:00–18:00)'
    PIGEON       = 'PIGEON',       'Голубь (равномерная активность)'


class Employee(models.Model):
    """
    Таблица `employees` — основная карточка сотрудника.
    ТЗ §6.2: ФИО (2–200 символов), tab_number, birth_date, контакты,
    фото, даты приёма/увольнения, статус, орг. инфо, рабочие параметры.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='employee_profile')

    # ── Основная информация ──
    last_name   = models.CharField(max_length=100)
    first_name  = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    tab_number  = models.CharField(max_length=30, unique=True,
                                   help_text='Уникальный табельный номер')
    birth_date  = models.DateField(null=True, blank=True)
    hire_date   = models.DateField(null=True, blank=True)
    fire_date   = models.DateField(null=True, blank=True)
    status      = models.CharField(max_length=20, choices=EmployeeStatus.choices,
                                   default=EmployeeStatus.ACTIVE)
    photo       = models.ImageField(upload_to='employees/photos/', null=True, blank=True)

    # ── Организационная информация ──
    department           = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                             null=True, related_name='primary_employees')
    position             = models.ForeignKey(Position, on_delete=models.SET_NULL,
                                             null=True, related_name='employees')
    grade                = models.CharField(max_length=20, choices=Grade.choices, default=Grade.MIDDLE)
    direct_manager       = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='direct_reports')
    functional_manager   = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='functional_reports')
    location_city        = models.CharField(max_length=100, blank=True)
    location_country     = models.CharField(max_length=100, blank=True, default='Russia')
    timezone             = models.CharField(max_length=60, default='Europe/Moscow')
    work_format          = models.CharField(max_length=20, choices=WorkFormat.choices,
                                            default=WorkFormat.OFFICE)

    # ── Рабочие параметры ──
    weekly_hours_norm    = models.PositiveIntegerField(default=40,
                                                       help_text='Норма часов в неделю')
    daily_hours_available= models.PositiveIntegerField(default=8)
    chronotype           = models.CharField(max_length=20, choices=Chronotype.choices,
                                            default=Chronotype.INTERMEDIATE)
    years_experience     = models.FloatField(default=0.0)

    # ── Текущая загрузка (кэш, обновляется воркером) ──
    current_load_percent = models.FloatField(default=0.0)

    # Audit
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_employees')
    updated_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='updated_employees')
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    belbin_role = models.CharField(
        max_length=30,
        default='SPECIALIST',
        choices=[('COORDINATOR', 'Координатор'),
                ('SHAPER', 'Мотиватор (Shaper)'),
                ('PLANT', 'Генератор идей (Plant)'),
                ('MONITOR_EVALUATOR', 'Аналитик (Monitor Evaluator)'),
                ('IMPLEMENTER', 'Реализатор (Implementer)'),
                ('COMPLETER_FINISHER', 'Педант (Completer Finisher)'),
                ('TEAMWORKER', 'Душа команды (Teamworker)'),
                ('RESOURCE_INVESTIGAROR', 'Исследователь ресурсов'),
                ('SPECIALIST', 'Специалист'),
            ],
            verbose_name="Роль по Белбину"
    )

    class Meta:
        db_table  = 'employees'
        ordering  = ['last_name', 'first_name']
        indexes   = [
            # TZ §8.3 — индекс по ФИО
            models.Index(name='emp_fio_idx', fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.middle_name}'.strip()


class EmployeeDepartment(models.Model):
    """
    Таблица `employee_departments` — матричная структура:
    сотрудник может принадлежать к нескольким отделам (ТЗ §6.2).
    """
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                   related_name='additional_departments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    since      = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'employee_departments'
        unique_together = ('employee', 'department')


class EmployeeContact(models.Model):
    """Таблица `employee_contacts` — контакты (телефон, email, Telegram)."""
    employee       = models.OneToOneField(Employee, on_delete=models.CASCADE,
                                          related_name='contacts')
    email          = models.EmailField(unique=True)
    phone          = models.CharField(max_length=30, blank=True)
    telegram       = models.CharField(max_length=100, blank=True)
    slack          = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'employee_contacts'


# ═══════════════════════════════════════════════════════════════════
#  SECTION 3 — Skills & Competencies (TZ §6.5)
# ═══════════════════════════════════════════════════════════════════

class SkillType(models.TextChoices):
    """5 типов навыков ТЗ §6.5."""
    HARD     = 'HARD',     'Hard Skill (Python, SQL, Figma)'
    SOFT     = 'SOFT',     'Soft Skill (коммуникация, лидерство)'
    TOOL     = 'TOOL',     'Tool (Jira, Git, Docker)'
    LANGUAGE = 'LANGUAGE', 'Language (English C1, Deutsch B2)'
    DOMAIN   = 'DOMAIN',   'Domain (финансы, медицина, логистика)'


class SkillCategory(models.Model):
    """Таблица `skill_categories` — иерархия категорий навыков."""
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent      = models.ForeignKey('self', on_delete=models.CASCADE,
                                    null=True, blank=True, related_name='children')

    class Meta:
        db_table = 'skill_categories'

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Таблица `skills` — справочник навыков. Уровни 1–5."""
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100)
    skill_type  = models.CharField(max_length=20, choices=SkillType.choices, default=SkillType.HARD)
    category    = models.ForeignKey(SkillCategory, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='skills')
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)

    # Audit
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    is_deleted  = models.BooleanField(default=False)

    class Meta:
        db_table = 'skills'
        indexes = [
            models.Index(fields=['skill_type'], name='skills_type_idx'),
        ]

    def __str__(self):
        return f'{self.name} [{self.skill_type}]'


class EmployeeSkill(models.Model):
    """
    Таблица `employee_skills`.
    TZ §6.5 — шкала 1–5, верификация, история.
    TZ §8.3 — составной индекс (skill_id, level DESC).
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee        = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='skills')
    skill           = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level           = models.PositiveSmallIntegerField(
                          default=1, help_text='1=новичок, 2=базовый, 3=средний, 4=продвинутый, 5=эксперт'
                      )
    # Верификация (самооценка → подтверждение руководителем/сертификатом)
    is_self_assessed = models.BooleanField(default=True)
    is_verified      = models.BooleanField(default=False)
    verified_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='verified_skills')
    verified_at      = models.DateTimeField(null=True, blank=True)
    verification_source = models.CharField(max_length=100, blank=True,
                                           help_text='Сертификат, рук-ль, результат проекта')
    note             = models.TextField(blank=True)

    # Audit
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_skills'
        unique_together = ('employee', 'skill')
        indexes = [
            # TZ §8.3 — составной индекс
            models.Index(fields=['skill', '-level'], name='emp_skills_skill_lvl_idx'),
        ]


class SkillEvaluation(models.Model):
    """Таблица `skill_evaluations` — история оценок навыка."""
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_skill  = models.ForeignKey(EmployeeSkill, on_delete=models.CASCADE,
                                         related_name='evaluations')
    level           = models.PositiveSmallIntegerField()
    evaluated_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    evaluated_at    = models.DateTimeField(auto_now_add=True)
    comment         = models.TextField(blank=True)

    class Meta:
        db_table = 'skill_evaluations'


class Certification(models.Model):
    """Таблица `certifications` — сертификации сотрудников со сроками действия."""
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='certifications')
    skill        = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    name         = models.CharField(max_length=200)
    issuer       = models.CharField(max_length=200, blank=True)
    issued_at    = models.DateField()
    expires_at   = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    file         = models.FileField(upload_to='certifications/', null=True, blank=True)

    class Meta:
        db_table = 'certifications'


class Language(models.Model):
    """Таблица `languages` — справочник языков."""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'languages'


class EmployeeLanguage(models.Model):
    """Таблица `employee_languages` — знание языков сотрудником."""
    class Level(models.TextChoices):
        A1 = 'A1', 'A1 — Начальный'
        A2 = 'A2', 'A2 — Элементарный'
        B1 = 'B1', 'B1 — Средний'
        B2 = 'B2', 'B2 — Выше среднего'
        C1 = 'C1', 'C1 — Продвинутый'
        C2 = 'C2', 'C2 — Владение в совершенстве'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='languages')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    level    = models.CharField(max_length=2, choices=Level.choices)

    class Meta:
        db_table = 'employee_languages'
        unique_together = ('employee', 'language')


# ═══════════════════════════════════════════════════════════════════
#  SECTION 4 — Work Preferences (TZ §6.4)
# ═══════════════════════════════════════════════════════════════════

class CommunicationStyle(models.TextChoices):
    SYNC  = 'SYNC',  'Синхронный'
    ASYNC = 'ASYNC', 'Асинхронный'
    MIXED = 'MIXED', 'Смешанный'


class TeamRole(models.TextChoices):
    LEADER      = 'LEADER',      'Лидер'
    EXECUTOR    = 'EXECUTOR',    'Исполнитель'
    COORDINATOR = 'COORDINATOR', 'Координатор'


class WorkPreference(models.Model):
    """
    Таблица `work_preferences` (employee_preferences).
    TZ §6.4 — хронотип, график, форматы, нежелательные задачи,
    взаимодействие с коллегами.
    """
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='preferences')

    # Рабочий день
    work_day_start   = models.TimeField(default='09:00')
    work_day_end     = models.TimeField(default='18:00')
    lunch_start      = models.TimeField(null=True, blank=True)
    max_continuous_work_hours = models.PositiveSmallIntegerField(default=4)

    # Отношение к встречам
    meetings_before_noon = models.BooleanField(default=True)
    meetings_after_18    = models.BooleanField(default=False)
    meetings_on_weekends = models.BooleanField(default=False)
    max_meeting_duration_min = models.PositiveSmallIntegerField(
        default=60, help_text='Мин: 30/60/90/120'
    )

    # Формат работы
    work_format = models.CharField(max_length=20, choices=WorkFormat.choices, default=WorkFormat.OFFICE)
    office_days_per_week = models.PositiveSmallIntegerField(default=5)

    # Типы задач
    preferred_task_types   = models.JSONField(default=list, blank=True)
    disliked_task_types    = models.JSONField(default=list, blank=True)
    ready_for_urgent_tasks = models.BooleanField(default=True)
    disliked_projects      = models.ManyToManyField('projects.Project', blank=True,
                                                     related_name='disliked_by')

    # Взаимодействие
    team_role            = models.CharField(max_length=20, choices=TeamRole.choices,
                                            default=TeamRole.EXECUTOR)
    preferred_team_size  = models.PositiveSmallIntegerField(default=5)
    communication_style  = models.CharField(max_length=10, choices=CommunicationStyle.choices,
                                            default=CommunicationStyle.MIXED)

    # Audit
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_preferences'


class ColleaguePreference(models.Model):
    """
    Таблица `compatibility_preferences` (colleague_preferences).
    TZ §6.4 — желаемые и нежелательные коллеги.
    """
    class PreferenceType(models.TextChoices):
        PREFERRED   = 'PREFERRED',   'Желаемый'
        UNDESIRED   = 'UNDESIRED',   'Нежелательный'

    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='colleague_preferences')
    colleague  = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='mentioned_in_preferences')
    pref_type  = models.CharField(max_length=20, choices=PreferenceType.choices)
    reason     = models.TextField(blank=True)

    class Meta:
        db_table = 'colleague_preferences'
        unique_together = ('employee', 'colleague')


class WorkSchedule(models.Model):
    """Таблица `work_schedules` — индивидуальный рабочий график."""
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    name     = models.CharField(max_length=100)
    # JSON: {mon: [start, end], tue: [...], ...}
    schedule = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    valid_from  = models.DateField()
    valid_until = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'work_schedules'


class ScheduleException(models.Model):
    """Таблица `schedule_exceptions` — исключения в графике (праздники, переработки)."""
    schedule  = models.ForeignKey(WorkSchedule, on_delete=models.CASCADE, related_name='exceptions')
    exception_date = models.DateField()
    is_working_day = models.BooleanField(default=False)
    note           = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'schedule_exceptions'
