from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/org/', include('apps.organization.urls')),
    path('api/v1/absences/', include('apps.absences.urls')),
    path('api/v1/projects/', include('apps.projects.urls')),
    path('api/v1/algorithm/', include('apps.algorithm.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls'))
]
