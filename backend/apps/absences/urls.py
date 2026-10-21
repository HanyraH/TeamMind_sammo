from django.urls import path
from .views import AbsenceCalendarView, AbsenceSubmitView

urlpatterns = [
    path('calendar/', AbsenceCalendarView.as_view(), name='absences_calendar'),
    path('submit/', AbsenceSubmitView.as_view(), name='absences_submit'),
]
