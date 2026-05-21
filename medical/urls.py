# medical/urls.py
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'medical'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='medical:doctor_list', permanent=False)),
    # Especialidades
    path('especialidades/', views.EspecialidadListView.as_view(), name='especialidad_list'),
    path('especialidades/new/', views.EspecialidadCreateView.as_view(), name='especialidad_create'),
    path('especialidades/<int:pk>/edit/', views.EspecialidadUpdateView.as_view(), name='especialidad_update'),

    # Médicos
    path('doctors/', views.DoctorListView.as_view(), name='doctor_list'),
    path('doctors/new/', views.DoctorCreateView.as_view(), name='doctor_create'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('doctors/<int:pk>/edit/', views.DoctorUpdateView.as_view(), name='doctor_update'),

    # Pacientes
    path('patients/', views.PatientListView.as_view(), name='patient_list'),
    path('patients/new/', views.PatientCreateView.as_view(), name='patient_create'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient_detail'),
    path('patients/<int:pk>/edit/', views.PatientUpdateView.as_view(), name='patient_update'),
    path('patients/<int:pk>/historia/', views.HistoriaClinicaView.as_view(), name='historia_clinica'),
]
