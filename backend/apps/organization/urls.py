from django.urls import path
from .views import EmployeeListView, ImportExportEmployeesView, EmployeeDetailView

urlpatterns = [
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/import-export/', ImportExportEmployeesView.as_view(), name='employee_import_export'),
    path('employees/<str:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
]

