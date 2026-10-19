from django.urls import path
from .views import DashboardKpiView, ExportAnalyticsReportView

urlpatterns = [
    path('kpi/', DashboardKpiView.as_view(), name='analytics_kpi'),
    path('export/', ExportAnalyticsReportView.as_view(), name='analytics_export'),
]
