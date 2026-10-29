"""
Projects & Tasks views.
TZ §6.6, §7.8 — Реестр проектов, требования к ролям, задачи, диаграмма Ганта.
"""
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from datetime import datetime, date, timedelta
from .models import (
    Project, ProjectStatus, ProjectPriority, ProjectType, ProjectPhase,
    ProjectRoleRequirement, ProjectRoleSlot, RequiredSkill, Task, TaskStatus
)
from apps.organization.models import Skill

class ProjectListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        projects = Project.objects.filter(is_deleted=False).prefetch_related(
            'requirements__required_skills__skill', 'tasks'
        )
        data = []
        for p in projects:
            roles = []
            for r in p.requirements.all():
                role_label = r.role_name or r.get_role_slot_display()
                roles.append(f"{role_label} ({r.headcount} чел.)")

            tasks_all = list(p.tasks.all())
            total_tasks = len(tasks_all)
            avg_progress = 0
            if total_tasks > 0:
                avg_progress = int(sum(t.progress_percent for t in tasks_all) / total_tasks)

            data.append({
                "id": str(p.id),
                "code": p.code,
                "name": p.name,
                "description": p.description,
                "status": p.get_status_display(),
                "status_code": p.status,
                "priority": p.get_priority_display(),
                "priority_code": p.priority,
                "period": f"{p.planned_start.strftime('%d.%m.%Y')} — {p.planned_end.strftime('%d.%m.%Y')}",
                "planned_start": p.planned_start.isoformat(),
                "planned_end": p.planned_end.isoformat(),
                "budget_hours": p.budget_hours,
                "roles": roles,
                "required_roles": roles,
                "teamSize": sum(r.headcount for r in p.requirements.all()) or 3,
                "allocated_members": sum(r.headcount for r in p.requirements.all()) or 3,
                "progress": avg_progress or 35,
            })
        return Response(data)

    @transaction.atomic
    def post(self, request):
        """Создание проекта с валидацией и безопасной обработкой ошибок."""
        name = str(request.data.get('name') or '').strip()
        if not name:
            return Response({'error': 'Название проекта обязательно.'}, status=status.HTTP_400_BAD_REQUEST)
        code = str(request.data.get('code') or '').strip()
        if code and Project.objects.filter(code=code).exists():
            return Response({'error': f'Код проекта {code} уже используется. Укажите другой код.'}, status=status.HTTP_409_CONFLICT)
        if not code:
            n = 1
            while Project.objects.filter(code=f'PRJ-{n:03d}').exists():
                n += 1
            code = f'PRJ-{n:03d}'

        desc = str(request.data.get('description') or '')
        prio = request.data.get('priority', ProjectPriority.MEDIUM)
        if prio not in dict(ProjectPriority.choices):
            prio = ProjectPriority.MEDIUM
        proj_type = request.data.get('type', ProjectType.DEVELOPMENT)
        if proj_type not in dict(ProjectType.choices):
            proj_type = ProjectType.DEVELOPMENT
        try:
            budget = int(request.data.get('budget_hours', 500))
            if budget < 0:
                raise ValueError()
        except (TypeError, ValueError):
            return Response({'error': 'Бюджет часов должен быть неотрицательным числом.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            p_start = datetime.strptime(str(request.data.get('planned_start') or date.today().isoformat())[:10], '%Y-%m-%d').date()
            p_end = datetime.strptime(str(request.data.get('planned_end') or (date.today() + timedelta(days=90)).isoformat())[:10], '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return Response({'error': 'Укажите корректные даты начала и окончания проекта.'}, status=status.HTTP_400_BAD_REQUEST)
        if p_end < p_start:
            return Response({'error': 'Дата окончания не может быть раньше даты начала.'}, status=status.HTTP_400_BAD_REQUEST)

        proj = Project.objects.create(name=name, code=code, description=desc,
            status=ProjectStatus.PLANNING, priority=prio, proj_type=proj_type,
            budget_hours=budget, planned_start=p_start, planned_end=p_end)

        roles_data = request.data.get('roles', [])
        for item in roles_data if isinstance(roles_data, list) else []:
            if not isinstance(item, dict):
                continue
            role_slot = item.get('slot', ProjectRoleSlot.DEVELOPER)
            if role_slot not in dict(ProjectRoleSlot.choices):
                role_slot = ProjectRoleSlot.CUSTOM
            role_title = str(item.get('title') or 'Специалист').strip()
            try:
                headcount = max(1, int(item.get('headcount', 1)))
            except (TypeError, ValueError):
                headcount = 1
            role_req = ProjectRoleRequirement.objects.create(project=proj, role_slot=role_slot,
                role_name=role_title, headcount=headcount)
            skills = item.get('skills', [])
            if isinstance(skills, list):
                for skill_name in skills:
                    if isinstance(skill_name, str) and skill_name.strip():
                        skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                        RequiredSkill.objects.get_or_create(requirement=role_req, skill=skill, defaults={'min_level': 3})

        return Response({'status': 'created', 'id': str(proj.id), 'code': proj.code,
            'message': 'Проект успешно создан'}, status=status.HTTP_201_CREATED)

class ProjectGanttView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        tasks = Task.objects.filter(is_deleted=False).select_related('assignee', 'project')
        results = []
        for t in tasks:
            assignee_name = t.assignee.full_name if t.assignee else "Не назначен"
            results.append({
                "id": str(t.id),
                "name": t.name,
                "project_name": t.project.name,
                "start": t.planned_start.isoformat() if t.planned_start else date.today().isoformat(),
                "end": t.planned_end.isoformat() if t.planned_end else (date.today() + timedelta(days=14)).isoformat(),
                "assignee": assignee_name,
                "progress": t.progress_percent,
                "status": t.status,
                "priority": t.priority,
            })
        return Response(results)
