from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.algorithm.engine import TeamMatchingEngine, DEFAULT_WEIGHTS
from apps.organization.models import Employee, Department, Position, Chronotype, Skill, EmployeeSkill
from apps.projects.models import Project, ProjectStatus, ProjectRoleRequirement, RequiredSkill


class TeamMatchingEngineTestCase(TestCase):
    def setUp(self):
        self.engine = TeamMatchingEngine()

    def test_default_weights(self):
        self.assertAlmostEqual(sum(self.engine.weights.values()), 1.0)
        self.assertAlmostEqual(self.engine.weights['K'], 0.35)
        self.assertAlmostEqual(self.engine.weights['A'], 0.25)
        self.assertAlmostEqual(self.engine.weights['L'], 0.20)
        self.assertAlmostEqual(self.engine.weights['T'], 0.10)
        self.assertAlmostEqual(self.engine.weights['C'], 0.10)

    def test_hard_constraints_fired(self):
        candidate = {
            'id': 1,
            'name': 'Fired User',
            'is_active': False,
            'status': 'FIRED',
            'availability_percent': 100.0,
            'skills_dict': {'Python': 5}
        }
        passed, reason = self.engine.filter_hard_constraints(candidate, {'id': 'P1'})
        self.assertFalse(passed)
        self.assertIn("уволен", reason)

    def test_hard_constraints_missing_required_skill(self):
        candidate = {
            'id': 2,
            'name': 'Junior Dev',
            'is_active': True,
            'status': 'ACTIVE',
            'availability_percent': 100.0,
            'skills_dict': {'Python': 1}
        }
        project_reqs = {
            'id': 'P1',
            'required_skills': {'Python': 4}
        }
        passed, reason = self.engine.filter_hard_constraints(candidate, project_reqs)
        self.assertFalse(passed)
        self.assertIn("Недостаточный уровень", reason)

    def test_score_calculation_formula(self):
        candidate = {
            'id': 3,
            'name': 'Senior Engineer',
            'is_active': True,
            'status': 'ACTIVE',
            'availability_percent': 100.0,
            'current_load_percent': 50.0,
            'chronotype': 'LARK',
            'skills_dict': {'Python': 5, 'Django': 4}
        }
        project_reqs = {
            'id': 'P1',
            'required_skills': {'Python': 4, 'Django': 4},
            'estimated_load_percent': 30.0,
            'target_chronotype': 'LARK'
        }
        res = self.engine.calculate_score(candidate, project_reqs)
        self.assertIn('total_score', res)
        self.assertGreater(res['total_score'], 70.0)

    def test_what_if_swap(self):
        current_team = [
            {'id': '1', 'name': 'Dev 1', 'role_assigned': 'Lead', 'final_score': 85.0},
            {'id': '2', 'name': 'Dev 2', 'role_assigned': 'Dev', 'final_score': 80.0},
        ]
        new_candidate = {
            'id': '3',
            'name': 'Dev 3',
            'current_load_percent': 40.0,
            'availability_percent': 80.0,
            'skills_dict': {'Python': 5},
            'chronotype': 'INTERMEDIATE'
        }
        result = self.engine.what_if_swap(current_team, old_member_id='2', new_candidate=new_candidate)
        self.assertIn('overall_match_score', result)
        self.assertIn('delta', result)
        self.assertIn('risk_assessment', result)
        self.assertEqual(len(result['updated_team']), 2)


class AlgorithmViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.dept = Department.objects.create(name='AI Lab', code='AI')
        self.pos = Position.objects.create(title='Algo Dev')
        self.emp = Employee.objects.create(
            first_name='Роман',
            last_name='Васильев',
            tab_number='EMP-099',
            department=self.dept,
            position=self.pos,
            chronotype=Chronotype.OWL,
            current_load_percent=60.0
        )
        self.project = Project.objects.create(
            name='Test Project',
            code='PRJ-TEST',
            planned_start='2026-11-01',
            planned_end='2027-02-01',
            status=ProjectStatus.PLANNING
        )

    def test_run_team_matching_api(self):
        response = self.client.post('/api/v1/algorithm/match/', {
            'project_id': str(self.project.id),
            'weights': {'K': 0.4, 'A': 0.2, 'L': 0.2, 'T': 0.1, 'C': 0.1}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('variants', response.data)
        self.assertGreaterEqual(len(response.data['variants']), 1)

    def test_what_if_simulation_api(self):
        response = self.client.post('/api/v1/algorithm/what-if/', {
            'current_team': [{'id': str(self.emp.id), 'name': self.emp.full_name}],
            'old_id': str(self.emp.id),
            'candidate_id': str(self.emp.id)
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overall_match_score', response.data)
