# appointments/forms.py
from django import forms
from django.utils import timezone

from medical.models import Especialidad, Medico

from .models import Cita, HorarioDisponible


class MedicoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'Dr(a). {obj.user.get_full_name()} — {obj.especialidad}'


class CitaForm(forms.ModelForm):
    medico = MedicoChoiceField(
        queryset=Medico.objects.select_related('user', 'especialidad').filter(
            especialidad__activa=True
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Médico',
    )

    class Meta:
        model = Cita
        fields = ['medico', 'fecha_hora', 'motivo']
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'motivo': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describa el motivo de la consulta...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_hora'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_fecha_hora(self):
        fecha_hora = self.cleaned_data.get('fecha_hora')
        if fecha_hora and fecha_hora <= timezone.now():
            raise forms.ValidationError('La fecha debe ser futura.')
        return fecha_hora


class CitaUpdateMedicoForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['estado', 'notas_medico']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas_medico': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'notas_medico': 'Notas del médico',
        }


class CitaFilterForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Desde',
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Hasta',
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Cita.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado',
    )
    medico = forms.ModelChoiceField(
        queryset=Medico.objects.select_related('user', 'especialidad'),
        required=False,
        empty_label='Todos los médicos',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Médico',
    )
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.filter(activa=True),
        required=False,
        empty_label='Todas las especialidades',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Especialidad',
    )


class HorarioForm(forms.ModelForm):
    class Meta:
        model = HorarioDisponible
        fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'activo']
        widgets = {
            'dia_semana': forms.Select(attrs={'class': 'form-select'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise forms.ValidationError(
                'La hora de fin debe ser posterior a la hora de inicio.'
            )
        return cleaned_data
