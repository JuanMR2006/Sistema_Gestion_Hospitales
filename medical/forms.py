# medical/forms.py
from django import forms

from users.models import CustomUser

from .models import Especialidad, HistoriaClinica, Medico, Paciente


class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ['nombre', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['user', 'especialidad', 'numero_licencia', 'consultorio', 'bio']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'especialidad': forms.Select(attrs={'class': 'form-select'}),
            'numero_licencia': forms.TextInput(attrs={'class': 'form-control'}),
            'consultorio': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        taken_ids = Medico.objects.values_list('user_id', flat=True)
        if self.instance and self.instance.pk:
            taken_ids = taken_ids.exclude(pk=self.instance.pk)
        self.fields['user'].queryset = CustomUser.objects.filter(
            role=CustomUser.MEDICO
        ).exclude(id__in=taken_ids)


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'user', 'fecha_nacimiento', 'genero', 'blood_type',
            'direccion', 'contacto_emergencia', 'telefono_emergencia',
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'blood_type': forms.Select(attrs={'class': 'form-select'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        taken_ids = Paciente.objects.values_list('user_id', flat=True)
        if self.instance and self.instance.pk:
            taken_ids = taken_ids.exclude(pk=self.instance.pk)
        self.fields['user'].queryset = CustomUser.objects.filter(
            role=CustomUser.PACIENTE
        ).exclude(id__in=taken_ids)


class HistoriaClinicaForm(forms.ModelForm):
    class Meta:
        model = HistoriaClinica
        fields = [
            'alergias', 'enfermedades_cronicas',
            'medicamentos_actuales', 'antecedentes_familiares',
        ]
        widgets = {
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enfermedades_cronicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medicamentos_actuales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'antecedentes_familiares': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PacienteSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, email o teléfono...',
        }),
    )
