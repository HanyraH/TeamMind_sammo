from django.contrib import admin
from .models import Project, Task

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'planned_start', 'planned_end')
    list_filter = ('status',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'priority', 'status', 'assignee')
    list_filter = ('priority', 'status')
    search_fields = ('name',)
