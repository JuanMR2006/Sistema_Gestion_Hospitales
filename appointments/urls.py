# appointments/urls.py
from django.urls import path

from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.CitaListView.as_view(), name='cita_list'),
    path('new/', views.CitaCreateView.as_view(), name='cita_create'),
    path('<int:pk>/', views.CitaDetailView.as_view(), name='cita_detail'),
    path('<int:pk>/edit/', views.CitaUpdateView.as_view(), name='cita_update'),
    path('<int:pk>/cancel/', views.CitaCancelView.as_view(), name='cita_cancel'),
    path('my/', views.MisCitasView.as_view(), name='mis_citas'),
    path('horarios/<int:medico_pk>/', views.HorarioListView.as_view(), name='horario_list'),
    path('horarios/<int:pk>/delete/', views.HorarioDeleteView.as_view(), name='horario_delete'),
]
