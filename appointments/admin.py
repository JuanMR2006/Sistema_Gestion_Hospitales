# appointments/admin.py
from django.contrib import admin

from .models import Cita, HorarioDisponible


@admin.register(HorarioDisponible)
class HorarioDisponibleAdmin(admin.ModelAdmin):
    list_display = ['medico', 'dia_semana', 'hora_inicio', 'hora_fin', 'activo']
    list_filter = ['activo', 'dia_semana', 'medico__especialidad']
    search_fields = ['medico__user__first_name', 'medico__user__last_name']


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'medico', 'fecha_hora', 'estado']
    list_filter = ['estado', 'medico__especialidad']
    search_fields = [
        'paciente__user__first_name', 'paciente__user__last_name',
        'medico__user__last_name',
    ]
    date_hierarchy = 'fecha_hora'
    readonly_fields = ['created_at', 'updated_at']
