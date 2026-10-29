from django.contrib import admin
from .models import Employee, Department, Skill, Position

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'chronotype', 'work_format')
    search_fields = ('last_name', 'first_name')
    list_filter = ('chronotype', 'work_format')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'skill_type', 'category')
    list_filter = ('skill_type',)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'grade', 'created_at')
    search_fields = ('title',)
