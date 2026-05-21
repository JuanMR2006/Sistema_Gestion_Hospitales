# dashboard/urls.py
from django.urls import path

from .charts import (
    citas_por_dia_semana,
    citas_por_especialidad,
    citas_por_estado,
    pacientes_por_mes,
)
from .views import (
    AdminPanelView,
    DashboardAdminView,
    DashboardMedicoView,
    DashboardPacienteView,
    DashboardRedirectView,
    SearchPacienteView,
)

app_name = 'dashboard'

urlpatterns = [
    # Dashboards por rol
    path('', DashboardRedirectView.as_view(), name='home'),
    path('dashboard/', DashboardAdminView.as_view(), name='admin_dashboard'),
    path('dashboard/medico/', DashboardMedicoView.as_view(), name='medico_dashboard'),
    path('dashboard/paciente/', DashboardPacienteView.as_view(), name='paciente_dashboard'),
    # Panel y búsqueda
    path('admin-panel/', AdminPanelView.as_view(), name='admin_panel'),
    path('search/pacientes/', SearchPacienteView.as_view(), name='search_pacientes'),
    # Chart API endpoints
    path('charts/citas-por-especialidad/', citas_por_especialidad, name='chart_especialidad'),
    path('charts/pacientes-por-mes/', pacientes_por_mes, name='chart_pacientes'),
    path('charts/citas-por-estado/', citas_por_estado, name='chart_estado'),
    path('charts/citas-por-dia/', citas_por_dia_semana, name='chart_dia'),
]
