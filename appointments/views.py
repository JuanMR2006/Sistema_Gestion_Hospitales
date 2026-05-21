# appointments/views.py
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from medical.models import Medico
from users.mixins import AdminRequiredMixin, PacienteRequiredMixin

from .forms import CitaFilterForm, CitaForm, CitaUpdateMedicoForm, HorarioForm
from .models import Cita, HorarioDisponible
from .utils import send_appointment_email

logger = logging.getLogger(__name__)


# ─── Citas ────────────────────────────────────────────────────────────────────

class CitaListView(LoginRequiredMixin, ListView):
    model = Cita
    template_name = 'appointments/cita_list.html'
    context_object_name = 'citas'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = Cita.objects.select_related(
            'paciente__user', 'medico__user', 'medico__especialidad'
        )
        if user.is_medico:
            qs = qs.filter(medico__user=user)
        elif user.is_paciente:
            qs = qs.filter(paciente__user=user)
        elif not user.is_admin:
            return qs.none()

        form = CitaFilterForm(self.request.GET or None)
        if form.is_valid():
            cd = form.cleaned_data
            if cd.get('fecha_inicio'):
                qs = qs.filter(fecha_hora__date__gte=cd['fecha_inicio'])
            if cd.get('fecha_fin'):
                qs = qs.filter(fecha_hora__date__lte=cd['fecha_fin'])
            if cd.get('estado'):
                qs = qs.filter(estado=cd['estado'])
            if cd.get('medico'):
                qs = qs.filter(medico=cd['medico'])
            if cd.get('especialidad'):
                qs = qs.filter(medico__especialidad=cd['especialidad'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = CitaFilterForm(self.request.GET or None)
        ctx['total'] = ctx['paginator'].count
        return ctx


class CitaCreateView(PacienteRequiredMixin, CreateView):
    model = Cita
    form_class = CitaForm
    template_name = 'appointments/cita_form.html'

    def form_valid(self, form):
        try:
            paciente = self.request.user.paciente_profile
        except Exception:
            messages.error(self.request, 'No tienes un perfil de paciente asociado.')
            return redirect(reverse('appointments:cita_list'))

        cita = form.save(commit=False)
        cita.paciente = paciente
        cita.save()

        try:
            send_appointment_email(cita, 'creada')
        except Exception as exc:
            logger.error('Error enviando email cita #%s: %s', cita.pk, exc)

        messages.success(self.request, 'Cita agendada correctamente.')
        return redirect(reverse('appointments:mis_citas'))


class CitaDetailView(LoginRequiredMixin, DetailView):
    model = Cita
    template_name = 'appointments/cita_detail.html'
    context_object_name = 'cita'

    def get(self, request, *args, **kwargs):
        cita = get_object_or_404(
            Cita.objects.select_related(
                'paciente__user', 'medico__user', 'medico__especialidad'
            ),
            pk=kwargs['pk'],
        )
        user = request.user
        has_access = (
            user.is_admin
            or (user.is_medico and getattr(user, 'medico_profile', None) == cita.medico)
            or (user.is_paciente and getattr(user, 'paciente_profile', None) == cita.paciente)
        )
        if not has_access:
            messages.error(request, 'No tienes permiso para ver esta cita.')
            return redirect(reverse('appointments:cita_list'))

        update_form = None
        if user.is_admin or user.is_medico:
            update_form = CitaUpdateMedicoForm(instance=cita)

        return render(request, self.template_name, {
            'cita': cita,
            'update_form': update_form,
            'can_cancel': (
                cita.estado not in (Cita.CANCELADA, Cita.COMPLETADA)
                and cita.fecha_hora > timezone.now()
            ),
        })


class CitaUpdateView(LoginRequiredMixin, View):
    template_name = 'appointments/cita_update.html'

    def _get_cita(self, pk):
        return get_object_or_404(
            Cita.objects.select_related(
                'paciente__user', 'medico__user', 'medico__especialidad'
            ),
            pk=pk,
        )

    def _has_permission(self, user, cita):
        return user.is_admin or (
            user.is_medico and getattr(user, 'medico_profile', None) == cita.medico
        )

    def _get_form_class(self, user):
        return CitaUpdateMedicoForm

    def get(self, request, pk):
        cita = self._get_cita(pk)
        if not self._has_permission(request.user, cita):
            messages.error(request, 'No tienes permiso para editar esta cita.')
            return redirect(reverse('appointments:cita_detail', kwargs={'pk': pk}))
        form = self._get_form_class(request.user)(instance=cita)
        return render(request, self.template_name, {'cita': cita, 'form': form})

    def post(self, request, pk):
        cita = self._get_cita(pk)
        if not self._has_permission(request.user, cita):
            messages.error(request, 'No tienes permiso para editar esta cita.')
            return redirect(reverse('appointments:cita_detail', kwargs={'pk': pk}))

        old_estado = cita.estado
        form = self._get_form_class(request.user)(request.POST, instance=cita)
        if form.is_valid():
            cita = form.save()
            if cita.estado != old_estado:
                try:
                    send_appointment_email(cita, cita.estado)
                except Exception as exc:
                    logger.error('Error enviando email: %s', exc)
            messages.success(request, 'Cita actualizada correctamente.')
            return redirect(reverse('appointments:cita_detail', kwargs={'pk': pk}))

        return render(request, self.template_name, {'cita': cita, 'form': form})


class CitaCancelView(LoginRequiredMixin, View):

    def post(self, request, pk):
        cita = get_object_or_404(Cita, pk=pk)
        user = request.user

        if user.is_paciente:
            if getattr(user, 'paciente_profile', None) != cita.paciente:
                messages.error(request, 'No tienes permiso para cancelar esta cita.')
                return redirect(reverse('appointments:mis_citas'))
        elif not (user.is_admin or user.is_medico):
            messages.error(request, 'No tienes permiso para cancelar esta cita.')
            return redirect(reverse('appointments:cita_list'))

        if cita.estado == Cita.COMPLETADA:
            messages.error(request, 'No se puede cancelar una cita ya completada.')
            return redirect(reverse('appointments:cita_detail', kwargs={'pk': pk}))

        if cita.fecha_hora <= timezone.now():
            messages.error(request, 'No se puede cancelar una cita que ya pasó.')
            return redirect(reverse('appointments:cita_detail', kwargs={'pk': pk}))

        if cita.estado == Cita.CANCELADA:
            messages.warning(request, 'La cita ya estaba cancelada.')
            return redirect(reverse('appointments:cita_detail', kwargs={'pk': pk}))

        cita.estado = Cita.CANCELADA
        cita.save(update_fields=['estado', 'updated_at'])

        try:
            send_appointment_email(cita, Cita.CANCELADA)
        except Exception as exc:
            logger.error('Error enviando email cancelación cita #%s: %s', pk, exc)

        messages.success(request, 'Cita cancelada correctamente.')
        if user.is_paciente:
            return redirect(reverse('appointments:mis_citas'))
        return redirect(reverse('appointments:cita_list'))


class MisCitasView(PacienteRequiredMixin, ListView):
    model = Cita
    template_name = 'appointments/mis_citas.html'
    context_object_name = 'citas'

    def _get_paciente_qs(self):
        try:
            paciente = self.request.user.paciente_profile
        except Exception:
            return Cita.objects.none()
        return Cita.objects.filter(paciente=paciente).select_related(
            'medico__user', 'medico__especialidad'
        )

    def get_queryset(self):
        return self._get_paciente_qs()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        qs = self._get_paciente_qs()
        ctx['proximas_citas'] = qs.filter(
            fecha_hora__gte=now
        ).exclude(estado=Cita.CANCELADA).order_by('fecha_hora')
        ctx['citas_pasadas'] = qs.filter(fecha_hora__lt=now).order_by('-fecha_hora')[:10]
        ctx['now'] = now
        return ctx


# ─── Horarios ────────────────────────────────────────────────────────────────

class HorarioListView(AdminRequiredMixin, View):
    template_name = 'appointments/horario_list.html'

    def _get_medico(self, medico_pk):
        return get_object_or_404(
            Medico.objects.select_related('user', 'especialidad'),
            pk=medico_pk,
        )

    def get(self, request, medico_pk):
        medico = self._get_medico(medico_pk)
        horarios = HorarioDisponible.objects.filter(medico=medico)
        form = HorarioForm()
        return render(request, self.template_name, {
            'medico': medico,
            'horarios': horarios,
            'form': form,
        })

    def post(self, request, medico_pk):
        medico = self._get_medico(medico_pk)
        form = HorarioForm(request.POST)
        if form.is_valid():
            try:
                horario = form.save(commit=False)
                horario.medico = medico
                horario.save()
                messages.success(request, 'Horario agregado correctamente.')
                return redirect(reverse('medical:doctor_detail', kwargs={'pk': medico_pk}))
            except IntegrityError:
                messages.error(request, 'Ya existe un horario con ese día y hora de inicio.')

        horarios = HorarioDisponible.objects.filter(medico=medico)
        return render(request, self.template_name, {
            'medico': medico,
            'horarios': horarios,
            'form': form,
        })


class HorarioDeleteView(AdminRequiredMixin, View):

    def post(self, request, pk):
        horario = get_object_or_404(HorarioDisponible, pk=pk)
        medico_pk = horario.medico_id
        horario.delete()
        messages.success(request, 'Horario eliminado correctamente.')
        return redirect(reverse('medical:doctor_detail', kwargs={'pk': medico_pk}))
