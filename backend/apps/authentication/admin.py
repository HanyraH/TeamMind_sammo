from django.contrib import admin
from .models import User, AuditLog, Session

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'entity', 'timestamp')
    list_filter = ('action', 'entity')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_active', 'created_at')
