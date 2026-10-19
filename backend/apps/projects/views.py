"""
Projects & Tasks views.
TZ §6.6, §7.8 — Реестр проектов, требования к ролям, задачи, диаграмма Ганта.
"""
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

    def post(self, request):
        """Создание нового проекта (ТЗ §6.6)"""
        name = request.data.get('name')
        code = request.data.get('code') or f"PRJ-{Project.objects.count() + 1:03d}"
        desc = request.data.get('description', '')
        prio = request.data.get('priority', ProjectPriority.MEDIUM)
        proj_type = request.data.get('type', ProjectType.DEVELOPMENT)
        budget = int(request.data.get('budget_hours', 500))

        if not name:
            return Response({'error': 'Название проекта обязательно'}, status=status.HTTP_400_BAD_REQUEST)

        start_str = request.data.get('planned_start')
        end_str = request.data.get('planned_end')
        try:
            p_start = datetime.strptime(start_str[:10], '%Y-%m-%d').date() if start_str else date.today()
            p_end = datetime.strptime(end_str[:10], '%Y-%m-%d').date() if end_str else date.today() + timedelta(days=90)
        except Exception:
            p_start = date.today()
            p_end = date.today() + timedelta(days=90)

        proj = Project.objects.create(
            name=name,
            code=code,
            description=desc,
            status=ProjectStatus.PLANNING,
            priority=prio,
            proj_type=proj_type,
            budget_hours=budget,
            planned_start=p_start,
            planned_end=p_end
        )

        # Создание ролей если переданы
        roles_data = request.data.get('roles', [])
        for r_item in roles_data:
            role_slot = r_item.get('slot', ProjectRoleSlot.DEVELOPER)
            role_title = r_item.get('title', 'Специалист')
            h_count = int(r_item.get('headcount', 1))
            role_req = ProjectRoleRequirement.objects.create(
                project=proj,
                role_slot=role_slot,
                role_name=role_title,
                headcount=h_count
            )
            for sk_name in r_item.get('skills', []):
                sk_obj, _ = Skill.objects.get_or_create(name=sk_name)
                RequiredSkill.objects.create(requirement=role_req, skill=sk_obj, min_level=3)

        return Response({
            "status": "created",
            "id": str(proj.id),
            "code": proj.code,
            "message": "Проект успешно создан"
        }, status=status.HTTP_201_CREATED)

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
