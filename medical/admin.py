# medical/admin.py
from django.contrib import admin

from .models import Especialidad, HistoriaClinica, Medico, Paciente


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre']


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ['user', 'especialidad', 'numero_licencia', 'consultorio']
    list_filter = ['especialidad']
    search_fields = ['user__first_name', 'user__last_name', 'numero_licencia']


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['user', 'genero', 'blood_type', 'fecha_nacimiento']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']


@admin.register(HistoriaClinica)
class HistoriaClinicaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'updated_at']
