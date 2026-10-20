from django.urls import path
from .views import ProjectListView, ProjectGanttView

urlpatterns = [
    path('', ProjectListView.as_view(), name='project_list'),
    path('gantt/', ProjectGanttView.as_view(), name='project_gantt_all'),
    path('<str:pk>/gantt/', ProjectGanttView.as_view(), name='project_gantt_single'),
]
