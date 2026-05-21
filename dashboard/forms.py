# dashboard/forms.py
from django import forms

from appointments.models import Cita
from medical.models import Especialidad, Medico


class AdminPanelFilterForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        label='Desde',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    fecha_fin = forms.DateField(
        required=False,
        label='Hasta',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    especialidad = forms.ModelChoiceField(
        required=False,
        label='Especialidad',
        queryset=Especialidad.objects.filter(activa=True),
        empty_label='Todas las especialidades',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    estado = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[('', 'Todos los estados')] + list(Cita.ESTADO_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    medico = forms.ModelChoiceField(
        required=False,
        label='Médico',
        queryset=Medico.objects.select_related('user', 'especialidad').all(),
        empty_label='Todos los médicos',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
