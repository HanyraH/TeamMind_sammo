from django.urls import path
from .views import RunTeamMatchingView, WhatIfSimulationView

urlpatterns = [
    path('match/', RunTeamMatchingView.as_view(), name='algo_match_team'),
    path('what-if/', WhatIfSimulationView.as_view(), name='algo_what_if'),
]
