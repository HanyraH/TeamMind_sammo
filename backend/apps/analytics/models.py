"""
Analytics, Load Tracking, Notifications, Settings models.
TZ §6.9, §8 — аналитическая панель, учёт времени, уведомления, справочники.

Tables (domain 9):
  meetings, work_hours_log (time_logs), overtime_records, load_snapshots,
  analytics_reports, notification_templates, notifications, audit_logs,
  time_zones, locations, production_calendar, settings
"""
import uuid
from django.db import models
from apps.authentication.models import User
from apps.organization.models import Employee, Department
from apps.projects.models import Project, Task


# ═══════════════════════════════════════════════════════════════════
#  Time Tracking
# ═══════════════════════════════════════════════════════════════════

class WorkHoursLog(models.Model):
    """
    Таблица `work_hours_log` (time_logs).
    TZ §8.3 — составной индекс (employee_id, work_date DESC).
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_logs')
    task         = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='work_logs')
    project      = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='work_logs')
    work_date    = models.DateField()
    hours_logged = models.DecimalField(max_digits=5, decimal_places=2)
    description  = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    is_deleted   = models.BooleanField(default=False)

    class Meta:
        db_table = 'work_hours_log'
        indexes = [
            # TZ §8.3
            models.Index(fields=['employee', '-work_date'], name='whl_emp_date_idx'),
        ]

    def __str__(self):
        return f'{self.employee} — {self.work_date}: {self.hours_logged}h'


class OvertimeRecord(models.Model):
    """Таблица `overtime_records` — фиксация переработок."""
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='overtime_records')
    project      = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    date         = models.DateField()
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2)
    reason       = models.TextField(blank=True)
    is_compensated = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'overtime_records'


class LoadSnapshot(models.Model):
    """
    Таблица `load_snapshots` — еженедельный снимок загрузки сотрудника.
    Используется для аналитики трендов и кэширования.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee         = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='load_snapshots')
    snapshot_date    = models.DateField(help_text='Дата снимка (начало недели)')
    load_percent     = models.FloatField(help_text='% загрузки за неделю')
    available_hours  = models.DecimalField(max_digits=5, decimal_places=2)
    scheduled_hours  = models.DecimalField(max_digits=5, decimal_places=2)
    projects_count   = models.PositiveSmallIntegerField(default=0)
    is_overloaded    = models.BooleanField(default=False, help_text='load > 80%')

    class Meta:
        db_table = 'load_snapshots'
        unique_together = ('employee', 'snapshot_date')
        indexes = [
            models.Index(fields=['snapshot_date', 'is_overloaded'], name='snap_date_ovl_idx'),
        ]


# ═══════════════════════════════════════════════════════════════════
#  Meetings
# ═══════════════════════════════════════════════════════════════════

class Meeting(models.Model):
    """Таблица `meetings` — рабочие встречи."""
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project      = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    starts_at    = models.DateTimeField()
    ends_at      = models.DateTimeField()
    participants = models.ManyToManyField(Employee, blank=True, related_name='meetings')
    organizer    = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                     related_name='organized_meetings')
    is_mandatory = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meetings'


# ═══════════════════════════════════════════════════════════════════
#  Analytics Reports
# ═══════════════════════════════════════════════════════════════════

class ReportType(models.TextChoices):
    DASHBOARD   = 'DASHBOARD',   'Главный дашборд'
    LOAD        = 'LOAD',        'Загрузка по отделам'
    SKILLS_GAP  = 'SKILLS_GAP',  'Анализ пробелов навыков'
    ABSENCES    = 'ABSENCES',    'Отчёт по отсутствиям'
    TEAM_STATS  = 'TEAM_STATS',  'Статистика команд'
    CUSTOM      = 'CUSTOM',      'Произвольный'


class AnalyticsReport(models.Model):
    """
    Таблица `analytics_reports`.
    TZ §6.9 — сохранённые отчёты с планировщиком экспорта PDF/Excel/CSV.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type  = models.CharField(max_length=30, choices=ReportType.choices)
    title        = models.CharField(max_length=200)
    parameters   = models.JSONField(default=dict,
                                    help_text='Фильтры: период, отдел, формат')
    result_data  = models.JSONField(default=dict)
    file         = models.FileField(upload_to='reports/', null=True, blank=True)
    export_format = models.CharField(max_length=10, default='PDF',
                                     help_text='PDF | EXCEL | CSV | PNG')
    created_at   = models.DateTimeField(auto_now_add=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_deleted   = models.BooleanField(default=False)
    deleted_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analytics_reports'
        ordering = ['-created_at']


# ═══════════════════════════════════════════════════════════════════
#  Notifications
# ═══════════════════════════════════════════════════════════════════

class NotificationTemplate(models.Model):
    """Таблица `notification_templates` — шаблоны уведомлений."""
    code    = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=255)
    body    = models.TextField()
    channel = models.CharField(max_length=20, default='IN_APP',
                               help_text='IN_APP | EMAIL | TELEGRAM')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'notification_templates'


class Notification(models.Model):
    """Таблица `notifications` — уведомления пользователям."""
    class Status(models.TextChoices):
        UNREAD = 'UNREAD', 'Непрочитано'
        READ   = 'READ',   'Прочитано'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template     = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True)
    title        = models.CharField(max_length=255)
    body         = models.TextField()
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.UNREAD)
    created_at   = models.DateTimeField(auto_now_add=True)
    read_at      = models.DateTimeField(null=True, blank=True)
    extra        = models.JSONField(default=dict)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status'], name='notif_recv_status_idx'),
        ]


# ═══════════════════════════════════════════════════════════════════
#  Reference Dictionaries (Справочники)
# ═══════════════════════════════════════════════════════════════════

class TimeZone(models.Model):
    """Таблица `time_zones` — справочник часовых поясов."""
    code   = models.CharField(max_length=60, unique=True)
    name   = models.CharField(max_length=100)
    offset = models.SmallIntegerField(help_text='UTC offset in minutes')

    class Meta:
        db_table = 'time_zones'


class Location(models.Model):
    """Таблица `locations` — справочник офисов и локаций."""
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name     = models.CharField(max_length=200)
    city     = models.CharField(max_length=100)
    country  = models.CharField(max_length=100, default='Russia')
    timezone = models.CharField(max_length=60, default='Europe/Moscow')
    address  = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'locations'


class ProductionCalendar(models.Model):
    """
    Таблица `production_calendar` — производственный календарь (праздники, выходные).
    Используется при расчёте рабочих дней в отсутствиях.
    """
    date       = models.DateField(unique=True)
    is_working = models.BooleanField(default=True)
    is_holiday = models.BooleanField(default=False)
    name       = models.CharField(max_length=100, blank=True,
                                  help_text='Название праздника, если применимо')
    country    = models.CharField(max_length=10, default='RU')

    class Meta:
        db_table = 'production_calendar'
        indexes = [
            models.Index(fields=['country', 'date'], name='prod_cal_country_date_idx'),
        ]


class SystemSetting(models.Model):
    """
    Таблица `settings` — глобальные настройки системы.
    TZ §5.1 — валюта, рабочие нормы, праздники, конфигурируются суперадмином.
    """
    key         = models.CharField(max_length=100, unique=True)
    value       = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    updated_at  = models.DateTimeField(auto_now=True)
    updated_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'settings'

    def __str__(self):
        return f'{self.key}={self.value}'
