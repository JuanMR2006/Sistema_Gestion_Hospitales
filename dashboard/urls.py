# dashboard/urls.py
from django.urls import path

from .views import (
    CitasPorDiaView,
    CitasPorEspecialidadView,
    CitasPorEstadoView,
    DashboardAdminView,
    DashboardMedicoView,
    DashboardPacienteView,
    DashboardRedirectView,
    PacientesPorMesView,
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardRedirectView.as_view(), name='home'),
    path('dashboard/', DashboardAdminView.as_view(), name='admin_dashboard'),
    path('dashboard/medico/', DashboardMedicoView.as_view(), name='medico_dashboard'),
    path('dashboard/paciente/', DashboardPacienteView.as_view(), name='paciente_dashboard'),
    # Chart API endpoints
    path('charts/citas-por-especialidad/', CitasPorEspecialidadView.as_view(), name='chart_especialidad'),
    path('charts/pacientes-por-mes/', PacientesPorMesView.as_view(), name='chart_pacientes_mes'),
    path('charts/citas-por-estado/', CitasPorEstadoView.as_view(), name='chart_estado'),
    path('charts/citas-por-dia/', CitasPorDiaView.as_view(), name='chart_dia'),
]
