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
        self.assertIn('resilience_score', result)
        self.assertIn('bus_factor', result)
        self.assertEqual(len(result['updated_team']), 2)

    def test_analyze_team_risks_and_bus_factor(self):
        team = [
            {'id': '1', 'name': 'Lead Dev', 'current_load_percent': 95.0, 'skills_dict': {'Python': 5, 'System Design': 5}},
            {'id': '2', 'name': 'Junior Dev', 'current_load_percent': 30.0, 'skills_dict': {'Python': 2}},
        ]
        project_roles = [
            {'role_title': 'Lead', 'required_skills': {'System Design': 4, 'Python': 4}},
            {'role_title': 'Security', 'required_skills': {'CyberSecurity': 3}}
        ]
        analysis = self.engine.analyze_team_risks(team, project_roles)
        self.assertIn('resilience_score', analysis)
        self.assertIn('bus_factor', analysis)
        self.assertIn('critical_skills_at_risk', analysis)
        self.assertIn('burnout_risk', analysis)
        self.assertIn('recommendations', analysis)
        
        # CyberSecurity is uncovered (Bus Factor = 0)
        uncovered = [item for item in analysis['critical_skills_at_risk'] if item['status'] == 'UNCOVERED']
        self.assertEqual(len(uncovered), 1)
        self.assertEqual(uncovered[0]['skill'], 'CyberSecurity')
        
        # System Design has only 1 person (Bus Factor = 1, SPOF)
        spof = [item for item in analysis['critical_skills_at_risk'] if item['status'] == 'CRITICAL_SPOF']
        self.assertEqual(len(spof), 1)
        self.assertEqual(spof[0]['skill'], 'System Design')
        
        # Lead has load 95% -> critical burnout risk
        self.assertEqual(analysis['burnout_risk']['risk_level'], 'HIGH')
        self.assertEqual(len(analysis['burnout_risk']['high_load_members']), 1)

    def test_genetic_algorithm_order_crossover_and_convergence(self):
        candidates = [
            {'id': i, 'name': f'Dev {i}', 'is_active': True, 'status': 'ACTIVE',
             'availability_percent': 100.0, 'current_load_percent': 40.0,
             'skills_dict': {'Python': (i % 5) + 1, 'Django': 4}}
            for i in range(1, 15)
        ]
        role_reqs = [
            {'role_title': 'Lead', 'required_skills': {'Python': 5}, 'headcount': 1},
            {'role_title': 'Dev', 'required_skills': {'Python': 3, 'Django': 3}, 'headcount': 2}
        ]
        team, history = self.engine.run_genetic(candidates, role_reqs, generations=15, return_convergence=True)
        self.assertEqual(len(team), 3)
        # Check no duplicates
        ids = [m['id'] for m in team]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(history), 15)
        self.assertGreaterEqual(history[-1]['best_fitness'], history[0]['best_fitness'])

    def test_simulate_monte_carlo_risks(self):
        team = [
            {'id': '1', 'name': 'Dev 1', 'current_load_percent': 50.0, 'skills_dict': {'Python': 5}},
            {'id': '2', 'name': 'Dev 2', 'current_load_percent': 60.0, 'skills_dict': {'React': 4}},
        ]
        mc_res = self.engine.simulate_monte_carlo_risks(team, iterations=100)
        self.assertIn('success_probability', mc_res)
        self.assertIn('risk_profile', mc_res)
        self.assertEqual(mc_res['iterations_run'], 100)
        self.assertGreaterEqual(mc_res['success_probability'], 0.0)
        self.assertLessEqual(mc_res['success_probability'], 100.0)

    def test_belbin_balance_analysis(self):
        balanced_team = [
            {'id': '1', 'name': 'Leader', 'belbin_role': 'COORDINATOR'},
            {'id': '2', 'name': 'Worker', 'belbin_role': 'IMPLEMENTER'},
            {'id': '3', 'name': 'Creator', 'belbin_role': 'PLANT'}
        ]
        res = self.engine.analyze_belbin_balance(balanced_team)
        self.assertEqual(res['balance_score'], 95.0)
        self.assertEqual(res['clusters']['ACTION'], 1)
        self.assertEqual(res['clusters']['PEOPLE'], 1)
        self.assertEqual(res['clusters']['THOUGHT'], 1)
        self.assertEqual(len(res['conflicts']), 0)





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

    def test_team_risks_api(self):
        response = self.client.post('/api/v1/algorithm/risks/', {
            'team': [{'id': str(self.emp.id), 'name': self.emp.full_name, 'current_load_percent': 60.0, 'skills_dict': {'Python': 4}}],
            'project_id': str(self.project.id)
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resilience_score', response.data)
        self.assertIn('bus_factor', response.data)
        self.assertIn('burnout_risk', response.data)

    def test_presets_api(self):
        response = self.client.get('/api/v1/algorithm/presets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('presets', response.data)
        self.assertGreaterEqual(len(response.data['presets']), 5)


