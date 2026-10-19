from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.organization.models import Employee, Department, Position, Chronotype
from apps.projects.models import Project, ProjectStatus


class AnalyticsViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.dept = Department.objects.create(name='AI Lab', code='AI')
        self.pos = Position.objects.create(title='Data Scientist')
        self.emp = Employee.objects.create(
            first_name='Роман',
            last_name='Васильев',
            tab_number='EMP-003',
            department=self.dept,
            position=self.pos,
            chronotype=Chronotype.OWL,
            current_load_percent=80.0
        )
        self.prj = Project.objects.create(
            name='TeamMind Analytics',
            code='PRJ-ANA',
            status=ProjectStatus.ACTIVE,
            planned_start='2026-10-01',
            planned_end='2027-01-01'
        )

    def test_dashboard_kpi_view(self):
        res = self.client.get('/api/v1/analytics/kpi/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('kpis', res.data)
        self.assertIn('department_loads', res.data)
        self.assertIn('workload_distribution', res.data)
        self.assertIn('chronotypes', res.data)
        self.assertEqual(res.data['workload_distribution']['total'], 1)

    def test_export_analytics_excel_view(self):
        res = self.client.get('/api/v1/analytics/export/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertGreater(len(res.content), 5000)
