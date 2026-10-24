from django.urls import path
from .views import RunTeamMatchingView, WhatIfSimulationView, TeamRiskAssessmentView

urlpatterns = [
    path('match/', RunTeamMatchingView.as_view(), name='algo_match_team'),
    path('what-if/', WhatIfSimulationView.as_view(), name='algo_what_if'),
    path('risks/', TeamRiskAssessmentView.as_view(), name='algo_team_risks'),
]

