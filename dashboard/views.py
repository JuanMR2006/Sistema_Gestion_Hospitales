# dashboard/views.py
import logging
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from appointments.models import Cita
from medical.models import Medico, Paciente
from users.mixins import AdminRequiredMixin, MedicoRequiredMixin, PacienteRequiredMixin

logger = logging.getLogger(__name__)


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_admin:
            return redirect(reverse('dashboard:admin_dashboard'))
        if user.is_medico:
            return redirect(reverse('dashboard:medico_dashboard'))
        if user.is_paciente:
            return redirect(reverse('dashboard:paciente_dashboard'))
        return redirect(reverse('users:login'))


class DashboardAdminView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now().date()
        hace_30_dias = timezone.now() - timedelta(days=30)

        context['total_pacientes'] = Paciente.objects.count()
        context['total_medicos'] = Medico.objects.count()
        context['citas_hoy'] = Cita.objects.filter(
            fecha_hora__date=hoy
        ).select_related('paciente__user', 'medico__user', 'medico__especialidad')
        context['citas_pendientes'] = Cita.objects.filter(estado='PENDIENTE').count()
        context['citas_confirmadas'] = Cita.objects.filter(estado='CONFIRMADA').count()
        context['citas_canceladas'] = Cita.objects.filter(estado='CANCELADA').count()
        context['citas_completadas'] = Cita.objects.filter(estado='COMPLETADA').count()
        context['nuevos_pacientes_mes'] = Paciente.objects.filter(
            user__created_at__gte=hace_30_dias
        ).count()
        context['ultimas_citas'] = Cita.objects.select_related(
            'paciente__user', 'medico__user', 'medico__especialidad'
        ).order_by('-created_at')[:10]
        top_medicos = list(
            Medico.objects.annotate(
                total_citas=Count('citas')
            ).order_by('-total_citas').select_related('user', 'especialidad')[:5]
        )
        context['top_medicos'] = top_medicos
        max_citas = top_medicos[0].total_citas if top_medicos else 0
        context['max_citas_medico'] = max(max_citas, 1)
        context['medicos_activos'] = Medico.objects.filter(user__is_active=True).count()
        context['total_citas'] = Cita.objects.count()
        return context


class DashboardMedicoView(MedicoRequiredMixin, TemplateView):
    template_name = 'dashboard/medico_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medico = self.request.user.medico_profile
        hoy = timezone.now().date()
        hace_30_dias = timezone.now() - timedelta(days=30)
        en_7_dias = timezone.now() + timedelta(days=7)

        context['medico'] = medico
        context['citas_hoy'] = Cita.objects.filter(
            medico=medico,
            fecha_hora__date=hoy,
        ).select_related(
            'paciente__user', 'medico__user', 'medico__especialidad'
        ).order_by('fecha_hora')
        context['proximas_citas'] = Cita.objects.filter(
            medico=medico,
            fecha_hora__gte=timezone.now(),
            fecha_hora__lte=en_7_dias,
            estado__in=['PENDIENTE', 'CONFIRMADA'],
        ).select_related('paciente__user', 'medico__especialidad').order_by('fecha_hora')
        context['total_pacientes_atendidos'] = Cita.objects.filter(
            medico=medico,
            estado='COMPLETADA',
        ).count()
        context['total_citas_mes'] = Cita.objects.filter(
            medico=medico,
            fecha_hora__gte=hace_30_dias,
        ).count()
        return context


class DashboardPacienteView(PacienteRequiredMixin, TemplateView):
    template_name = 'dashboard/paciente_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paciente = self.request.user.paciente_profile
        ahora = timezone.now()

        context['paciente'] = paciente
        context['proximas_citas'] = Cita.objects.filter(
            paciente=paciente,
            fecha_hora__gte=ahora,
        ).exclude(estado='CANCELADA').select_related(
            'medico__user', 'medico__especialidad'
        ).order_by('fecha_hora')
        context['ultima_cita'] = Cita.objects.filter(
            paciente=paciente,
            estado='COMPLETADA',
        ).select_related(
            'medico__user', 'medico__especialidad'
        ).order_by('-fecha_hora').first()
        context['total_citas'] = Cita.objects.filter(paciente=paciente).count()
        context['citas_pendientes'] = Cita.objects.filter(
            paciente=paciente,
            estado='PENDIENTE',
        ).count()
        return context
