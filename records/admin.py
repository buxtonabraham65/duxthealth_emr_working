from django.contrib import admin
from .models import Patient, VitalSign, Consultation, Outreach, Note

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'dob', 'community', 'phone', 'date_registered')
    search_fields = ('full_name', 'phone', 'community')
    list_filter = ('gender', 'community')
    ordering = ('-date_registered',)

@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ('patient', 'bp_systolic', 'bp_diastolic', 'temp_c', 'bmi', 'date_recorded')
    search_fields = ('patient__full_name',)
    list_filter = ('date_recorded',)

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'diagnosis', 'created_at')
    search_fields = ('patient__full_name', 'diagnosis')
    list_filter = ('created_at',)

@admin.register(Outreach)
class OutreachAdmin(admin.ModelAdmin):
    list_display = ('location', 'date', 'created_by')
    search_fields = ('location', 'summary')
    list_filter = ('date',)

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('patient', 'diagnosis', 'created_at')
    search_fields = ('patient__full_name', 'diagnosis')
    list_filter = ('created_at',)
