# medical/views.py
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from users.mixins import AdminOrMedicoMixin, AdminRequiredMixin

from .forms import (
    EspecialidadForm,
    HistoriaClinicaForm,
    MedicoForm,
    PacienteForm,
    PacienteSearchForm,
)
from .models import Especialidad, HistoriaClinica, Medico, Paciente

logger = logging.getLogger(__name__)


# ─── Especialidad ─────────────────────────────────────────────────────────────

class EspecialidadListView(AdminRequiredMixin, ListView):
    model = Especialidad
    template_name = 'medical/especialidad_list.html'
    context_object_name = 'especialidades'


class EspecialidadCreateView(AdminRequiredMixin, CreateView):
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'medical/especialidad_form.html'
    success_url = reverse_lazy('medical:especialidad_list')

    def form_valid(self, form):
        messages.success(self.request, 'Especialidad creada correctamente.')
        return super().form_valid(form)


class EspecialidadUpdateView(AdminRequiredMixin, UpdateView):
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'medical/especialidad_form.html'
    success_url = reverse_lazy('medical:especialidad_list')

    def get_object(self, queryset=None):
        return get_object_or_404(Especialidad, pk=self.kwargs['pk'])

    def form_valid(self, form):
        messages.success(self.request, 'Especialidad actualizada correctamente.')
        return super().form_valid(form)


# ─── Médico ───────────────────────────────────────────────────────────────────

class DoctorListView(AdminRequiredMixin, ListView):
    model = Medico
    template_name = 'medical/doctor_list.html'
    context_object_name = 'medicos'
    paginate_by = 10

    def get_queryset(self):
        qs = Medico.objects.select_related('user', 'especialidad')
        especialidad_id = self.request.GET.get('especialidad', '').strip()
        if especialidad_id:
            qs = qs.filter(especialidad_id=especialidad_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['especialidades'] = Especialidad.objects.filter(activa=True)
        ctx['especialidad_seleccionada'] = self.request.GET.get('especialidad', '')
        return ctx


class DoctorCreateView(AdminRequiredMixin, CreateView):
    model = Medico
    form_class = MedicoForm
    template_name = 'medical/doctor_form.html'
    success_url = reverse_lazy('medical:doctor_list')

    def form_valid(self, form):
        try:
            medico = form.save(commit=False)
            user = medico.user
            user.role = user.__class__.MEDICO
            user.save(update_fields=['role'])
            medico.save()
            messages.success(self.request, f'Médico {medico} registrado correctamente.')
            return redirect(self.success_url)
        except IntegrityError as exc:
            logger.error('IntegrityError al crear médico: %s', exc)
            messages.error(self.request, 'Error: ya existe un perfil médico con esos datos.')
            return self.form_invalid(form)


class DoctorUpdateView(AdminRequiredMixin, UpdateView):
    model = Medico
    form_class = MedicoForm
    template_name = 'medical/doctor_form.html'
    success_url = reverse_lazy('medical:doctor_list')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Medico.objects.select_related('user', 'especialidad'),
            pk=self.kwargs['pk'],
        )

    def form_valid(self, form):
        messages.success(self.request, 'Datos del médico actualizados correctamente.')
        return super().form_valid(form)


class DoctorDetailView(AdminOrMedicoMixin, DetailView):
    model = Medico
    template_name = 'medical/doctor_detail.html'
    context_object_name = 'medico'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Medico.objects.select_related('user', 'especialidad'),
            pk=self.kwargs['pk'],
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['horarios'] = []
        try:
            ctx['horarios'] = list(
                self.object.horarios.all()
            )
        except AttributeError:
            pass
        return ctx


# ─── Paciente ─────────────────────────────────────────────────────────────────

class PatientListView(AdminOrMedicoMixin, ListView):
    model = Paciente
    template_name = 'medical/patient_list.html'
    context_object_name = 'pacientes'
    paginate_by = 10

    def get_queryset(self):
        qs = Paciente.objects.select_related('user')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__email__icontains=q)
                | Q(user__phone__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = PacienteSearchForm(self.request.GET or None)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class PatientCreateView(AdminRequiredMixin, CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'medical/patient_form.html'
    success_url = reverse_lazy('medical:patient_list')

    def form_valid(self, form):
        try:
            paciente = form.save(commit=False)
            user = paciente.user
            user.role = user.__class__.PACIENTE
            user.save(update_fields=['role'])
            paciente.save()
            HistoriaClinica.objects.create(paciente=paciente)
            messages.success(self.request, f'Paciente {paciente} registrado correctamente.')
            return redirect(self.success_url)
        except IntegrityError as exc:
            logger.error('IntegrityError al crear paciente: %s', exc)
            messages.error(self.request, 'Error: ya existe un perfil de paciente con esos datos.')
            return self.form_invalid(form)


class PatientUpdateView(AdminRequiredMixin, UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'medical/patient_form.html'
    success_url = reverse_lazy('medical:patient_list')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Paciente.objects.select_related('user'),
            pk=self.kwargs['pk'],
        )

    def form_valid(self, form):
        messages.success(self.request, 'Datos del paciente actualizados correctamente.')
        return super().form_valid(form)


class PatientDetailView(AdminOrMedicoMixin, DetailView):
    model = Paciente
    template_name = 'medical/patient_detail.html'
    context_object_name = 'paciente'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Paciente.objects.select_related('user'),
            pk=self.kwargs['pk'],
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx['historia'] = self.object.historia_clinica
        except HistoriaClinica.DoesNotExist:
            ctx['historia'] = None
        ctx['ultimas_citas'] = []
        try:
            ctx['ultimas_citas'] = list(
                self.object.citas.select_related('medico__user').order_by('-fecha')[:5]
            )
        except AttributeError:
            pass
        return ctx


# ─── Historia Clínica ─────────────────────────────────────────────────────────

class HistoriaClinicaView(LoginRequiredMixin, View):

    def _get_historia(self, pk):
        return get_object_or_404(
            HistoriaClinica.objects.select_related('paciente__user'),
            paciente__pk=pk,
        )

    def _check_paciente_access(self, request, paciente):
        """Returns True if access is allowed, False otherwise."""
        user = request.user
        if not (user.is_admin or user.is_medico):
            try:
                own = user.paciente_profile
            except Exception:
                return False
            if own.pk != paciente.pk:
                return False
        return True

    def get(self, request, pk):
        historia = self._get_historia(pk)
        paciente = historia.paciente

        if not self._check_paciente_access(request, paciente):
            messages.error(request, 'Solo puedes ver tu propia historia clínica.')
            return redirect('/')

        can_edit = request.user.is_admin or request.user.is_medico
        form = HistoriaClinicaForm(instance=historia)
        return render(request, 'medical/historia_clinica.html', {
            'historia': historia,
            'paciente': paciente,
            'form': form,
            'can_edit': can_edit,
        })

    def post(self, request, pk):
        historia = self._get_historia(pk)
        user = request.user

        if not (user.is_admin or user.is_medico):
            messages.error(request, 'No tienes permiso para editar la historia clínica.')
            return redirect(reverse('medical:historia_clinica', kwargs={'pk': pk}))

        form = HistoriaClinicaForm(request.POST, instance=historia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Historia clínica actualizada correctamente.')
            return redirect(reverse('medical:historia_clinica', kwargs={'pk': pk}))

        messages.error(request, 'Error al guardar. Revisa los datos ingresados.')
        return render(request, 'medical/historia_clinica.html', {
            'historia': historia,
            'paciente': historia.paciente,
            'form': form,
            'can_edit': True,
        })
