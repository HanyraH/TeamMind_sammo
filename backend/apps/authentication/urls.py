from django.urls import path
from .views import Verify2FAView, UserProfileView

urlpatterns = [
    path('2fa/verify/', Verify2FAView.as_view(), name='auth_verify_2fa'),
    path('me/', UserProfileView.as_view(), name='auth_profile_me'),
]
