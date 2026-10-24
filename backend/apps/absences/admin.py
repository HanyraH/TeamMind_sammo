from django.contrib import admin
from .models import Absence, AbsenceApproval, AbsenceDocument

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'absence_type', 'start_date', 'end_date', 'status')
    list_filter = ('absence_type', 'status')

@admin.register(AbsenceApproval)
class AbsenceApprovalAdmin(admin.ModelAdmin):
    list_display = ('id', 'absence', 'approver', 'step', 'decision', 'decided_at')
    list_filter = ('decision',)

@admin.register(AbsenceDocument)
class AbsenceDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'absence', 'name', 'uploaded_by', 'uploaded_at')
