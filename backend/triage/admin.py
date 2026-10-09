from django.contrib import admin

from .models import Patient, VitalMeasurement


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('reference', 'full_name', 'age', 'sex', 'created_at')
    search_fields = ('reference', 'full_name')
    readonly_fields = ('reference', 'created_at')


@admin.register(VitalMeasurement)
class VitalMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'systolic_bp', 'diastolic_bp', 'pulse',
        'temperature_c', 'spo2', 'source', 'measured_at',
    )
    list_filter = ('source',)
    date_hierarchy = 'measured_at'
