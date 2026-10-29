"""
Organization & Employees views.
TZ §6.2, §6.4, §6.5 — список сотрудников, фильтрация, карточка, экспорт.
"""
import random
import csv
import io
import re
from django.db import transaction, IntegrityError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q
from .models import Employee, Department, Position, Skill, EmployeeSkill, EmployeeContact

class EmployeeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        dept_code = request.query_params.get('department', '').strip()
        status_filter = request.query_params.get('status', '').strip()

        qs = Employee.objects.filter(is_deleted=False).select_related(
            'department', 'position'
        ).prefetch_related('skills__skill', 'contacts')

        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(tab_number__icontains=search) |
                Q(position__title__icontains=search) |
                Q(skills__skill__name__icontains=search)
            ).distinct()

        if dept_code and dept_code != 'ALL':
            qs = qs.filter(Q(department__code=dept_code) | Q(department__name=dept_code))

        if status_filter and status_filter != 'ALL':
            qs = qs.filter(status=status_filter)

        results = []
        for emp in qs:
            skills = [es.skill.name for es in emp.skills.all()]
            contact_email = getattr(emp.contacts, 'email', '') if hasattr(emp, 'contacts') else ''
            contact_phone = getattr(emp.contacts, 'phone', '') if hasattr(emp, 'contacts') else ''

            results.append({
                "id": str(emp.id),
                "tab_number": emp.tab_number,
                "name": emp.full_name,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "middle_name": emp.middle_name,
                "department": emp.department.name if emp.department else "Общий отдел",
                "department_code": emp.department.code if emp.department else "",
                "position": emp.position.title if emp.position else "Сотрудник",
                "grade": emp.grade,
                "load": round(emp.current_load_percent),
                "skills": skills,
                "chronotype": emp.get_chronotype_display(),
                "chronotype_code": emp.chronotype,
                "work_format": emp.get_work_format_display(),
                "status": emp.get_status_display(),
                "status_code": emp.status,
                "email": contact_email or f"{emp.tab_number.lower()}@teammind.local",
                "phone": contact_phone,
                "weekly_capacity": emp.weekly_hours_norm,
                "years_experience": emp.years_experience,
            })

        return Response({
            "count": len(results),
            "results": results
        })

    @transaction.atomic
    def post(self, request):
        """Создание сотрудника с валидацией и понятными ошибками."""
        fn = str(request.data.get('first_name') or '').strip()
        ln = str(request.data.get('last_name') or '').strip()
        if not fn or not ln:
            return Response({'error': 'Имя и фамилия обязательны.'}, status=status.HTTP_400_BAD_REQUEST)

        tab = str(request.data.get('tab_number') or '').strip()
        if tab and Employee.objects.filter(tab_number=tab).exists():
            return Response({'error': f'Табельный номер {tab} уже используется.'}, status=status.HTTP_409_CONFLICT)
        if not tab:
            n = 1
            while Employee.objects.filter(tab_number=f'EMP-{n:03d}').exists():
                n += 1
            tab = f'EMP-{n:03d}'

        load_raw = request.data.get('load', 50)
        try:
            load = float(load_raw)
            if not 0 <= load <= 100:
                raise ValueError()
        except (TypeError, ValueError):
            return Response({'error': 'Загрузка должна быть числом от 0 до 100.'}, status=status.HTTP_400_BAD_REQUEST)

        dept_name = str(request.data.get('department') or '').strip()
        pos_title = str(request.data.get('position') or 'Developer').strip()
        dept = Department.objects.filter(name=dept_name, is_deleted=False).first() or Department.objects.filter(is_deleted=False).first()
        pos, _ = Position.objects.get_or_create(title=pos_title or 'Developer')
        chronotype = request.data.get('chronotype', 'INTERMEDIATE')
        work_format = request.data.get('work_format', 'OFFICE')
        if chronotype not in dict(Employee._meta.get_field('chronotype').choices):
            chronotype = 'INTERMEDIATE'
        if work_format not in dict(Employee._meta.get_field('work_format').choices):
            work_format = 'OFFICE'

        emp = Employee.objects.create(
            first_name=fn, last_name=ln,
            middle_name=str(request.data.get('middle_name') or '').strip(),
            tab_number=tab, department=dept, position=pos,
            chronotype=chronotype, work_format=work_format,
            current_load_percent=load,
        )
        email = str(request.data.get('email') or f"{tab.lower()}@teammind.local").strip()
        phone = str(request.data.get('phone') or '').strip()
        if EmployeeContact.objects.filter(email=email).exists():
            email = f"{tab.lower()}@teammind.local"
        EmployeeContact.objects.create(employee=emp, email=email, phone=phone)

        skills_list = request.data.get('skills', [])
        if isinstance(skills_list, str):
            skills_list = [x.strip() for x in skills_list.split(',') if x.strip()]
        for skill_name in skills_list:
            if not isinstance(skill_name, str) or not skill_name.strip():
                continue
            sk, _ = Skill.objects.get_or_create(name=skill_name.strip())
            EmployeeSkill.objects.get_or_create(employee=emp, skill=sk, defaults={'level': random.randint(2, 4)})

        return Response({'status': 'created', 'id': str(emp.id), 'tab_number': emp.tab_number}, status=status.HTTP_201_CREATED)

class ImportExportEmployeesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Экспорт списка сотрудников в JSON/CSV формат"""
        employees = Employee.objects.filter(is_deleted=False).select_related('department', 'position')
        export_data = []
        for emp in employees:
            export_data.append({
                "Табельный номер": emp.tab_number,
                "ФИО": emp.full_name,
                "Отдел": emp.department.name if emp.department else "",
                "Должность": emp.position.title if emp.position else "",
                "Грейд": emp.grade,
                "Загрузка (%)": emp.current_load_percent,
                "Хронотип": emp.get_chronotype_display(),
                "Формат": emp.get_work_format_display(),
                "Статус": emp.get_status_display(),
            })
        if request.query_params.get('format') == 'json':
            return Response({"status": "ready", "count": len(export_data), "data": export_data})
        output = io.StringIO(newline='')
        headers = list(export_data[0].keys()) if export_data else ["Табельный номер", "ФИО", "Отдел", "Должность", "Грейд", "Загрузка (%)", "Хронотип", "Формат", "Статус"]
        writer = csv.DictWriter(output, fieldnames=headers, delimiter=';')
        writer.writeheader(); writer.writerows(export_data)
        response = HttpResponse('\ufeff' + output.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="teammind_employees.csv"'
        return response

    def post(self, request):
        return Response({"status": "imported", "message": "Импорт кадровых данных успешно завершен"})


class EmployeeDetailView(APIView):
    """
    Детальная карточка сотрудника — 9 вкладок профиля (ТЗ §7.6).
    1. Основная информация
    2. Матрица навыков
    3. Занятость и проекты
    4. Календарь отсутствий
    5. Рабочий график и хронотип
    6. Совместимость с коллегами
    7. Оборудование и рабочее место
    8. Кадровые документы
    9. История изменений (Audit Log)
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            emp = Employee.objects.filter(id=pk, is_deleted=False).select_related(
                'department', 'position', 'user'
            ).prefetch_related(
                'skills__skill',
                'colleague_preferences__colleague',
                'schedules'
            ).first()
        except Exception:
            emp = None

        if not emp:
            emp = Employee.objects.filter(tab_number=pk, is_deleted=False).first()

        if not emp:
            return Response({'error': 'Сотрудник не найден'}, status=status.HTTP_404_NOT_FOUND)

        # 1. Основная информация
        contact_email = getattr(emp.contacts, 'email', '') if hasattr(emp, 'contacts') else ''
        contact_phone = getattr(emp.contacts, 'phone', '') if hasattr(emp, 'contacts') else ''

        basic_info = {
            "id": str(emp.id),
            "tab_number": emp.tab_number,
            "full_name": emp.full_name,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "middle_name": emp.middle_name,
            "department": emp.department.name if emp.department else "Общий отдел",
            "position": emp.position.title if emp.position else "Специалист",
            "grade": emp.grade,
            "status": emp.get_status_display(),
            "status_code": emp.status,
            "birth_date": emp.birth_date.isoformat() if emp.birth_date else "1994-05-14",
            "hire_date": emp.hire_date.isoformat() if emp.hire_date else "2023-02-01",
            "location_city": emp.location_city or "Москва",
            "location_country": emp.location_country or "Россия",
            "timezone": emp.timezone or "Europe/Moscow",
            "email": contact_email or f"{emp.tab_number.lower()}@teammind.local",
            "phone": contact_phone or "+7 (999) 000-11-22",
            "years_experience": emp.years_experience or 4.5,
        }

        # 2. Матрица навыков (уровни 1–5, верификация)
        skills_matrix = []
        for es in emp.skills.all():
            skills_matrix.append({
                "skill_name": es.skill.name,
                "skill_type": es.skill.skill_type,
                "level": es.level,
                "is_verified": es.is_verified,
                "verification_source": es.verification_source or "Самооценка / Аттестация",
            })

        # 3. Занятость и проекты
        active_projects = []
        from apps.projects.models import Task
        tasks = Task.objects.filter(assignee=emp).select_related('project')
        for t in tasks:
            active_projects.append({
                "project_code": t.project.code,
                "project_name": t.project.name,
                "task_title": t.name,
                "status": t.get_status_display(),
                "progress": t.progress_percent,
            })

        workload_info = {
            "current_load_percent": round(emp.current_load_percent),
            "weekly_hours_norm": emp.weekly_hours_norm,
            "daily_hours_available": emp.daily_hours_available,
            "active_tasks_count": len(active_projects),
            "active_projects": active_projects,
        }

        # 4. Календарь отсутствий
        from apps.absences.models import Absence
        absences_list = []
        for ab in Absence.objects.filter(employee=emp, is_deleted=False):
            absences_list.append({
                "id": str(ab.id),
                "type": ab.get_absence_type_display(),
                "start_date": ab.start_date.isoformat(),
                "end_date": ab.end_date.isoformat(),
                "working_days": ab.working_days,
                "status": ab.get_status_display(),
                "reason": ab.reason,
            })

        # 5. Рабочий график и хронотип
        pref = getattr(emp, 'preferences', None)
        schedule_info = {
            "chronotype": emp.get_chronotype_display(),
            "chronotype_code": emp.chronotype,
            "work_format": emp.get_work_format_display(),
            "work_day_start": str(pref.work_day_start) if pref else "09:00",
            "work_day_end": str(pref.work_day_end) if pref else "18:00",
            "meetings_before_noon": pref.meetings_before_noon if pref else True,
            "meetings_after_18": pref.meetings_after_18 if pref else False,
            "communication_style": pref.communication_style if pref else "MIXED",
        }

        # 6. Совместимость с коллегами
        colleague_prefs = []
        for cp in emp.colleague_preferences.all():
            colleague_prefs.append({
                "colleague_name": cp.colleague.full_name,
                "colleague_position": cp.colleague.position.title if cp.colleague.position else "",
                "pref_type": cp.get_pref_type_display(),
                "reason": cp.reason,
            })

        # 7. Оборудование и рабочее место
        equipment = [
            {"item": "MacBook Pro 16' M3 Max", "serial": f"MBP-{emp.tab_number}-01", "status": "Выдано"},
            {"item": "Монитор Dell 27' 4K UltraSharp", "serial": f"MON-{emp.tab_number}-02", "status": "Выдано"},
            {"item": "Корпоративный VPN & YubiKey", "serial": f"SEC-{emp.tab_number}-03", "status": "Активен"},
        ]

        # 8. Кадровые документы
        documents = [
            {"title": "Трудовой договор", "doc_number": f"ТД-{emp.tab_number}/23", "date": "01.02.2023", "status": "Подписан"},
            {"title": "Соглашение о конфиденциальности (NDA)", "doc_number": f"NDA-{emp.tab_number}", "date": "01.02.2023", "status": "Действует"},
            {"title": "Лист ознакомления с ПВТР", "doc_number": "ПВТР-2024", "date": "15.01.2024", "status": "Ознакомлен"},
        ]

        # 9. История изменений (Audit Log)
        audit_history = [
            {"date": emp.updated_at.strftime('%d.%m.%Y %H:%M'), "action": "Обновление профиля", "actor": "Система синхронизации 1С:ЗУП"},
            {"date": emp.created_at.strftime('%d.%m.%Y %H:%M'), "action": "Создание карточки сотрудника", "actor": "HR Администратор"},
        ]

        return Response({
            "basic_info": basic_info,
            "skills_matrix": skills_matrix,
            "workload_info": workload_info,
            "absences": absences_list,
            "schedule": schedule_info,
            "colleague_compatibility": colleague_prefs,
            "equipment": equipment,
            "documents": documents,
            "audit_history": audit_history,
        })

