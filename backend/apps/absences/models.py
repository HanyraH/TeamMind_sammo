"""
Absences models.
TZ §6.3 — 16 базовых типов отсутствий, жизненный цикл статусов,
цепочки согласования, документы.

Tables: absence_types (enum), absences, absence_documents, absence_approvals
"""
import uuid
from django.db import models
from apps.authentication.models import User
from apps.organization.models import Employee


# ═══════════════════════════════════════════════════════════════════
#  Enums (TZ §6.3)
# ═══════════════════════════════════════════════════════════════════

class AbsenceType(models.TextChoices):
    """
    16 типов отсутствий согласно ТЗ §6.3.
    Коды соответствуют спецификации дословно.
    """
    ANNUAL     = 'ANNUAL',     'Ежегодный оплачиваемый отпуск'
    UNPAID     = 'UNPAID',     'Отпуск за свой счёт (без сохранения ЗП)'
    SICK       = 'SICK',       'Личный больничный'
    SICK_CHILD = 'SICK_CHILD', 'Больничный по уходу за ребёнком / членом семьи'
    MATERNITY  = 'MATERNITY',  'Декретный отпуск'
    PARENTAL   = 'PARENTAL',   'Отпуск по уходу за ребёнком'
    STUDY      = 'STUDY',      'Учебный отпуск'
    BUSINESS   = 'BUSINESS',   'Служебная командировка'
    REMOTE_DAY = 'REMOTE_DAY', 'Удалённый день вне графика (REMOTE_WORK)'
    DAY_OFF    = 'DAY_OFF',    'Отгул'
    COMP_TIME  = 'COMP_TIME',  'Отгул за переработку (компенсация)'
    QUARANTINE = 'QUARANTINE', 'Карантин / медицинское обследование'
    TRAINING   = 'TRAINING',   'Корпоративное обучение / повышение квалиф.'
    PERSONAL   = 'PERSONAL',   'Личные обстоятельства (вкл. донорские дни DONOR)'
    SUSPENSION = 'SUSPENSION', 'Отстранение / простой (IDLE) / гос. обязанности (DUTY)'
    OTHER      = 'OTHER',      'Прочее отсутствие'


class AbsenceStatus(models.TextChoices):
    """Жизненный цикл статусов — ТЗ §6.3."""
    DRAFT       = 'DRAFT',       'Черновик'
    PENDING     = 'PENDING',     'Ожидает подтверждения'
    APPROVED    = 'APPROVED',    'Одобрено'
    REJECTED    = 'REJECTED',    'Отклонено'
    CANCELLED   = 'CANCELLED',   'Отменено сотрудником'
    IN_PROGRESS = 'IN_PROGRESS', 'Текущий период'
    COMPLETED   = 'COMPLETED',   'Завершено'
    EXTENDED    = 'EXTENDED',    'Продлено'


# Влияние на загрузку по типу отсутствия (ТЗ §6.3, колонка «Влияние на загрузку»)
ABSENCE_LOAD_IMPACT: dict[str, str] = {
    AbsenceType.ANNUAL:     'FULL',     # полностью исключает
    AbsenceType.UNPAID:     'FULL',
    AbsenceType.SICK:       'FULL',
    AbsenceType.SICK_CHILD: 'FULL',
    AbsenceType.MATERNITY:  'FULL',
    AbsenceType.PARENTAL:   'FULL',
    AbsenceType.STUDY:      'FULL',
    AbsenceType.BUSINESS:   'PARTIAL',  # доступен % часов
    AbsenceType.REMOTE_DAY: 'NONE',     # работает удалённо
    AbsenceType.DAY_OFF:    'FULL',
    AbsenceType.COMP_TIME:  'FULL',
    AbsenceType.QUARANTINE: 'FULL',
    AbsenceType.TRAINING:   'PARTIAL',
    AbsenceType.PERSONAL:   'FULL',
    AbsenceType.SUSPENSION: 'FULL',
    AbsenceType.OTHER:      'FULL',
}

# Требуется документ по типу (ТЗ §6.3)
ABSENCE_REQUIRES_DOC: set[str] = {
    AbsenceType.SICK,
    AbsenceType.SICK_CHILD,
    AbsenceType.MATERNITY,
    AbsenceType.PARENTAL,
    AbsenceType.STUDY,
    AbsenceType.BUSINESS,
    AbsenceType.QUARANTINE,
    AbsenceType.SUSPENSION,
}


# ═══════════════════════════════════════════════════════════════════
#  Models
# ═══════════════════════════════════════════════════════════════════

class Absence(models.Model):
    """
    Таблица `absences`.
    TZ §6.3 — основная запись об отсутствии сотрудника.
    Поддерживает производственный календарь и пересечения.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='absences')
    absence_type = models.CharField(max_length=20, choices=AbsenceType.choices)
    status       = models.CharField(max_length=20, choices=AbsenceStatus.choices,
                                    default=AbsenceStatus.DRAFT)
    start_date   = models.DateField()
    end_date     = models.DateField()
    # Рабочие дни рассчитываются автоматически с учётом производственного календаря
    working_days = models.PositiveIntegerField(default=0)
    # Для командировок и обучения — процент доступности
    availability_percent = models.PositiveSmallIntegerField(
        default=0, help_text='0=недоступен, 1–99=частично, 100=полностью доступен'
    )
    reason       = models.TextField(blank=True)
    comment      = models.TextField(blank=True, help_text='Комментарий руководителя')

    # Audit
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='created_absences')
    is_deleted   = models.BooleanField(default=False)
    deleted_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'absences'
        indexes  = [
            # TZ §8.3 — индекс на диапазон дат
            models.Index(fields=['start_date', 'end_date'], name='abs_date_range_idx'),
            models.Index(fields=['employee', 'status'], name='abs_emp_status_idx'),
        ]
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.employee} — {self.absence_type} ({self.start_date}..{self.end_date})'

    @property
    def requires_document(self) -> bool:
        return self.absence_type in ABSENCE_REQUIRES_DOC

    @property
    def load_impact(self) -> str:
        return ABSENCE_LOAD_IMPACT.get(self.absence_type, 'FULL')


class AbsenceDocument(models.Model):
    """Таблица `absence_documents` — подтверждающие документы."""
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    absence = models.ForeignKey(Absence, on_delete=models.CASCADE, related_name='documents')
    file    = models.FileField(upload_to='absences/documents/')
    name    = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'absence_documents'


class AbsenceApproval(models.Model):
    """
    Таблица `absence_approvals` — цепочка согласования.
    Один шаг согласования: руководитель → статус решения.
    """
    class Decision(models.TextChoices):
        PENDING  = 'PENDING',  'Ожидает'
        APPROVED = 'APPROVED', 'Одобрено'
        REJECTED = 'REJECTED', 'Отклонено'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    absence    = models.ForeignKey(Absence, on_delete=models.CASCADE, related_name='approvals')
    approver   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='absence_approvals')
    step       = models.PositiveSmallIntegerField(default=1, help_text='Шаг цепочки согласования')
    decision   = models.CharField(max_length=10, choices=Decision.choices, default=Decision.PENDING)
    comment    = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'absence_approvals'
        ordering = ['step']
        unique_together = ('absence', 'approver', 'step')
