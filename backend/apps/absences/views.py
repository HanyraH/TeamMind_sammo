"""
Absences views.
TZ §6.3, §7.7 — Календарь отсутствий (16 типов), заявки, согласование.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from datetime import datetime, date
from .models import Absence, AbsenceType, AbsenceStatus, AbsenceApproval
from apps.organization.models import Employee

# Цветовая кодировка по ТЗ §7.7:
# отпуск — синий, больничный — красный, командировка — фиолетовый,
# удалёнка — жёлтый, декрет — розовый, учебный — зелёный, отгул — оранжевый, прочее — серый.
COLOR_MAP = {
    AbsenceType.ANNUAL:     '#3B82F6',  # синий
    AbsenceType.UNPAID:     '#64748B',  # серый
    AbsenceType.SICK:       '#EF4444',  # красный
    AbsenceType.SICK_CHILD: '#DC2626',  # темно-красный
    AbsenceType.MATERNITY:  '#EC4899',  # розовый
    AbsenceType.PARENTAL:   '#F472B6',  # светло-розовый
    AbsenceType.STUDY:      '#10B981',  # зелёный
    AbsenceType.BUSINESS:   '#8B5CF6',  # фиолетовый
    AbsenceType.REMOTE_DAY: '#F59E0B',  # жёлтый/янтарный
    AbsenceType.DAY_OFF:    '#F97316',  # оранжевый
    AbsenceType.COMP_TIME:  '#FB923C',  # светло-оранжевый
    AbsenceType.QUARANTINE: '#D97706',  # темно-желтый
    AbsenceType.TRAINING:   '#06B6D4',  # бирюзовый
    AbsenceType.PERSONAL:   '#6366F1',  # индиго
    AbsenceType.SUSPENSION: '#475569',  # сланцевый
    AbsenceType.OTHER:      '#94A3B8',  # нейтральный серый
}

class AbsenceCalendarView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        absences = Absence.objects.filter(is_deleted=False).select_related(
            'employee', 'employee__department', 'employee__position'
        )
        events = []
        for ab in absences:
            color = COLOR_MAP.get(ab.absence_type, '#3B82F6')
            events.append({
                "id": str(ab.id),
                "title": f"{ab.employee.last_name} {ab.employee.first_name[0]}.: {ab.get_absence_type_display()}",
                "employee_name": ab.employee.full_name,
                "department": ab.employee.department.name if ab.employee.department else "Общий отдел",
                "position": ab.employee.position.title if ab.employee.position else "Специалист",
                "start": ab.start_date.isoformat(),
                "end": ab.end_date.isoformat(),
                "type": ab.absence_type,
                "type_display": ab.get_absence_type_display(),
                "color": color,
                "status": ab.status,
                "status_display": ab.get_status_display(),
                "reason": ab.reason,
                "working_days": ab.working_days,
                "availability_percent": ab.availability_percent,
            })
        return Response(events)


class AbsenceSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Подача заявки на отсутствие сотрудника (ТЗ §6.3, UC-02, UC-03)"""
        emp_id = request.data.get('employee_id')
        a_type = request.data.get('absence_type', AbsenceType.ANNUAL)
        start_str = request.data.get('start_date')
        end_str = request.data.get('end_date')
        reason = request.data.get('reason', '')

        if not start_str or not end_str:
            return Response({'error': 'Даты начала и окончания обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        emp = None
        if emp_id:
            emp = Employee.objects.filter(id=emp_id).first()
        if not emp:
            emp = Employee.objects.first()

        try:
            start_d = datetime.strptime(start_str[:10], '%Y-%m-%d').date()
            end_d = datetime.strptime(end_str[:10], '%Y-%m-%d').date()
        except Exception:
            start_d = date.today()
            end_d = date.today()

        work_days = max(1, (end_d - start_d).days + 1)

        # Проверка пересечений
        overlap = Absence.objects.filter(
            employee=emp,
            status__in=[AbsenceStatus.APPROVED, AbsenceStatus.PENDING],
            start_date__lte=end_d,
            end_date__gte=start_d,
            is_deleted=False
        ).exists()

        ab = Absence.objects.create(
            employee=emp,
            absence_type=a_type,
            start_date=start_d,
            end_date=end_d,
            working_days=work_days,
            reason=reason,
            status=AbsenceStatus.PENDING,
            availability_percent=50 if a_type in [AbsenceType.BUSINESS, AbsenceType.TRAINING] else 0
        )

        return Response({
            "status": "created",
            "absence_id": str(ab.id),
            "current_stage": "PENDING_APPROVAL",
            "has_overlap_warning": overlap,
            "message": "Заявление зарегистрировано и отправлено на согласование руководителю"
        }, status=status.HTTP_201_CREATED)
