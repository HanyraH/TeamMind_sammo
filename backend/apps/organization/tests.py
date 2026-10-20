from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.organization.models import Employee, Department, Position, Chronotype, WorkFormat, EmployeeStatus


class OrganizationViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.dept = Department.objects.create(name='Backend Core', code='BC')
        self.pos = Position.objects.create(title='Lead Developer')
        self.emp = Employee.objects.create(
            first_name='Дмитрий',
            last_name='Соколов',
            tab_number='EMP-001',
            department=self.dept,
            position=self.pos,
            grade='LEAD',
            status=EmployeeStatus.ACTIVE,
            chronotype=Chronotype.LARK,
            work_format=WorkFormat.OFFICE,
            current_load_percent=85.0
        )

    def test_employee_list_view(self):
        res = self.client.get('/api/v1/org/employees/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['tab_number'], 'EMP-001')

    def test_employee_detail_view_9_tabs(self):
        res = self.client.get(f'/api/v1/org/employees/{self.emp.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected_keys = [
            'basic_info', 'skills_matrix', 'workload_info', 'absences',
            'schedule', 'colleague_compatibility', 'equipment', 'documents', 'audit_history'
        ]
        for key in expected_keys:
            self.assertIn(key, res.data)
        self.assertEqual(res.data['basic_info']['full_name'], self.emp.full_name)

    def test_employee_create_view(self):
        payload = {
            'first_name': 'Анна',
            'last_name': 'Смирнова',
            'department': 'Backend Core',
            'position': 'Middle Developer',
            'skills': ['Python', 'Django'],
            'chronotype': 'INTERMEDIATE',
            'work_format': 'REMOTE',
            'load': 60
        }
        res = self.client.post('/api/v1/org/employees/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 2)
