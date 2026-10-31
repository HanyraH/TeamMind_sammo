"""
Algorithm views: TeamMatching and What-If simulation.
TZ §6.8 — Алгоритм формирования команд (Математическая модель).
Интеграция с базой данных (Employee, Project, ProjectRoleRequirement, Skills).
"""
import uuid
from typing import Dict, Any, List
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch

from apps.organization.models import Employee, Chronotype
from apps.projects.models import Project, ProjectRoleRequirement, RequiredSkill
from apps.absences.models import Absence, AbsenceStatus, AbsenceType
from .engine import TeamMatchingEngine, DEFAULT_WEIGHTS


def _build_candidate_dict(emp: Employee) -> Dict[str, Any]:
    """Преобразует модель Employee в словарь кандидата для TeamMatchingEngine."""
    skills_dict = {es.skill.name: es.level for es in emp.skills.all()}
    
    # Предпочтения
    disliked_projects = []
    preferred_projects = []
    if hasattr(emp, 'preferences') and emp.preferences:
        disliked_projects = [str(p.id) for p in emp.preferences.disliked_projects.all()]
    
    # Совместимость с коллегами
    colleagues_affinity = {}
    for cp in emp.colleague_preferences.all():
        colleagues_affinity[str(cp.colleague_id)] = 1.0 if cp.pref_type == 'PREFERRED' else -1.0

    # Проверка критических отсутствий
    has_critical_absence = (emp.status in ['FIRED', 'MATERNITY'])
    
    load = float(emp.current_load_percent or 0.0)
    avail = max(0.0, 100.0 - load) if emp.status == 'ACTIVE' else 0.0

    return {
        "id": str(emp.id),
        "name": emp.full_name,
        "full_name": emp.full_name,
        "tab_number": emp.tab_number,
        "department": emp.department.name if emp.department else "Общий отдел",
        "position": emp.position.title if emp.position else "Специалист",
        "grade": emp.grade,
        "status": emp.status,
        "is_active": (emp.status != 'FIRED' and not emp.is_deleted),
        "chronotype": emp.chronotype,
        "chronotype_display": emp.get_chronotype_display(),
        "current_load_percent": load,
        "availability_percent": avail,
        "skills_dict": skills_dict,
        "disliked_projects": disliked_projects,
        "preferred_projects": preferred_projects,
        "has_critical_absence": has_critical_absence,
        "has_critical_project_conflict": False,
        "colleagues_affinity": colleagues_affinity,
    }


def _get_project_role_requirements(project: Project) -> List[Dict[str, Any]]:
    """Извлекает требования к ролям проекта из БД."""
    requirements = project.requirements.all().prefetch_related(
        Prefetch('required_skills', queryset=RequiredSkill.objects.select_related('skill'))
    )
    role_reqs = []
    
    for req in requirements:
        req_skills = {rs.skill.name: rs.min_level for rs in req.required_skills.all()}
        # Если headcount > 1, создаем слоты для каждого участника
        for slot_idx in range(max(1, req.headcount)):
            role_reqs.append({
                "role_id": f"{req.id}_{slot_idx}",
                "role_title": req.role_name or req.get_role_slot_display(),
                "role_slot": req.role_slot,
                "required_skills": req_skills,
                "estimated_load_percent": round((req.hours_per_week / 40.0) * 100.0, 1) if req.hours_per_week else 50.0,
                "target_chronotype": "ANY"
            })

    # Если у проекта нет заданных требований, формируем базовый инженерный стек
    if not role_reqs:
        role_reqs = [
            {
                "role_id": "slot_lead",
                "role_title": "Lead Backend Engineer",
                "role_slot": "TEAM_LEAD",
                "required_skills": {"Django": 3, "Python": 4},
                "estimated_load_percent": 60.0,
                "target_chronotype": "LARK"
            },
            {
                "role_id": "slot_frontend",
                "role_title": "Senior Frontend Developer",
                "role_slot": "DEVELOPER",
                "required_skills": {"React": 3, "TypeScript": 3},
                "estimated_load_percent": 50.0,
                "target_chronotype": "INTERMEDIATE"
            },
            {
                "role_id": "slot_algo",
                "role_title": "Data & Algorithm Engineer",
                "role_slot": "DEVELOPER",
                "required_skills": {"Celery": 2, "Python": 3},
                "estimated_load_percent": 50.0,
                "target_chronotype": "OWL"
            },
            {
                "role_id": "slot_devops",
                "role_title": "DevOps & QA Engineer",
                "role_slot": "DEVOPS",
                "required_skills": {"Docker": 2, "Playwright": 2},
                "estimated_load_percent": 40.0,
                "target_chronotype": "INTERMEDIATE"
            }
        ]
        
    return role_reqs


class RunTeamMatchingView(APIView):
    """
    Запуск алгоритма подбора вариантов команд (ТЗ §6.8).
    Поддерживает жадную и генетическую оптимизацию по 5 стратегиям.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        project_id = request.data.get('project_id')
        user_weights = request.data.get('weights')
        count = int(request.data.get('count', 3))

        # Поиск проекта в БД
        project = None
        if project_id:
            try:
                project = Project.objects.filter(id=uuid.UUID(str(project_id)), is_deleted=False).first()
            except Exception:
                project = Project.objects.filter(code=str(project_id), is_deleted=False).first()

        if not project:
            project = Project.objects.filter(is_deleted=False).first()

        if not project:
            return Response(
                {"error": "Нет активных проектов в базе данных"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Подготовка весов
        weights = dict(DEFAULT_WEIGHTS)
        if user_weights and isinstance(user_weights, dict):
            for k in ['K', 'A', 'L', 'T', 'C']:
                if k in user_weights:
                    try:
                        weights[k] = float(user_weights[k])
                    except (ValueError, TypeError):
                        pass

        # Извлечение кандидатов из БД
        emp_qs = Employee.objects.filter(is_deleted=False).select_related(
            'department', 'position'
        ).prefetch_related(
            'skills__skill',
            'colleague_preferences',
            'preferences__disliked_projects'
        )
        
        candidates = [_build_candidate_dict(emp) for emp in emp_qs]
        role_reqs = _get_project_role_requirements(project)

        # Вызов движка с поддержкой пресетов
        user_preset = request.data.get('preset')
        engine = TeamMatchingEngine(weights=weights if user_weights else None, preset=user_preset)
        variants = engine.generate_all_variants(candidates, role_reqs, count=count)

        return Response({
            "project_id": str(project.id),
            "project_code": project.code,
            "project_name": project.name,
            "preset_used": getattr(engine, 'current_preset', 'CUSTOM'),
            "weights_used": engine.weights,
            "candidates_considered": len(candidates),
            "roles_count": len(role_reqs),
            "variants": variants
        })


class WhatIfSimulationView(APIView):
    """
    Интерактивный What-If симулятор (ТЗ §6.8).
    Мгновенный перерасчет метрик при замене участника в конструкторе
    + выдача списка подходящих кандидатов на замену.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Возвращает список доступных кандидатов для замены."""
        exclude_ids = request.query_params.getlist('exclude_ids')
        emp_qs = Employee.objects.filter(is_deleted=False).exclude(
            id__in=[uuid.UUID(i) for i in exclude_ids if len(i) == 36]
        ).select_related('department', 'position').prefetch_related('skills__skill')[:30]

        candidates = []
        for emp in emp_qs:
            candidates.append({
                "id": str(emp.id),
                "name": emp.full_name,
                "position": emp.position.title if emp.position else "Сотрудник",
                "department": emp.department.name if emp.department else "",
                "load": round(emp.current_load_percent),
                "chronotype": emp.get_chronotype_display(),
                "skills": [es.skill.name for es in emp.skills.all()[:4]]
            })

        return Response({"candidates": candidates})

    def post(self, request):
        current_team = request.data.get('current_team', [])
        old_member_id = request.data.get('old_id')
        new_candidate_data = request.data.get('candidate')
        new_candidate_id = request.data.get('candidate_id')
        user_weights = request.data.get('weights')

        engine = TeamMatchingEngine(weights=user_weights)

        # Если передан ID кандидата из БД, загружаем его профиль
        candidate_obj = None
        if new_candidate_id:
            emp = Employee.objects.filter(id=new_candidate_id, is_deleted=False).select_related(
                'department', 'position'
            ).prefetch_related('skills__skill').first()
            if emp:
                candidate_obj = _build_candidate_dict(emp)

        if not candidate_obj and isinstance(new_candidate_data, dict):
            candidate_obj = new_candidate_data
        elif not candidate_obj:
            # Возьмем случайного подходящего сотрудника не из current_team
            current_ids = [str(m.get('id')) for m in current_team if m.get('id')]
            fallback_emp = Employee.objects.filter(
                is_deleted=False, status='ACTIVE'
            ).exclude(
                id__in=[uuid.UUID(i) for i in current_ids if len(i) == 36]
            ).first()
            if fallback_emp:
                candidate_obj = _build_candidate_dict(fallback_emp)
            else:
                candidate_obj = {
                    "id": "candidate_sub",
                    "name": "Новый кандидат",
                    "current_load_percent": 50.0,
                    "availability_percent": 50.0,
                    "skills_dict": {"Django": 4, "React": 3},
                    "chronotype": "INTERMEDIATE"
                }

        # Выполняем What-If расчет
        result = engine.what_if_swap(
            current_team=current_team,
            old_member_id=old_member_id,
            new_candidate=candidate_obj,
            project_reqs=request.data.get('project_reqs')
        )

        return Response(result)


class TeamRiskAssessmentView(APIView):
    """
    Комплексная оценка рисков, Bus Factor и устойчивости команды (ТЗ §6.8).
    Принимает текущий состав команды и требования к ролям проекта.
    Возвращает Resilience Score, Single Point of Failure (SPOF) и рекомендации.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        team = request.data.get('team', [])
        role_requirements = request.data.get('role_requirements')
        project_id = request.data.get('project_id')

        if project_id and not role_requirements:
            try:
                project = Project.objects.filter(id=uuid.UUID(str(project_id)), is_deleted=False).first()
            except Exception:
                project = Project.objects.filter(code=str(project_id), is_deleted=False).first()
            if project:
                role_requirements = _get_project_role_requirements(project)

        engine = TeamMatchingEngine()
        risks = engine.analyze_team_risks(team=team, role_requirements=role_requirements)
        return Response(risks)


class AlgorithmPresetsView(APIView):
    """
    Получение списка доступных пресетов динамической калибровки весов (ТЗ §6.8).
    Поддерживает пресеты: BALANCED, CRUNCH, MENTORSHIP, FAST_PACE, DISTRIBUTED_SYNC.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        presets = TeamMatchingEngine.list_presets()
        return Response({"presets": presets})


