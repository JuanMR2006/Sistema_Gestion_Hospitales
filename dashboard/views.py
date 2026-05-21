# dashboard/views.py
import logging
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import ExtractIsoWeekDay, TruncMonth
from django.http import JsonResponse
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


# ── Chart API endpoints ────────────────────────────────────────────────────

class CitasPorEspecialidadView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        data = (
            Cita.objects.values('medico__especialidad__nombre')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        colors = [
            '#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0',
            '#6f42c1', '#fd7e14', '#20c997', '#d63384', '#6c757d',
        ]
        labels = [d['medico__especialidad__nombre'] or 'Sin especialidad' for d in data]
        counts = [d['total'] for d in data]
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Citas',
                'data': counts,
                'backgroundColor': colors[:len(labels)],
            }],
        })


class PacientesPorMesView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        hace_6_meses = timezone.now() - timedelta(days=180)
        data = (
            Paciente.objects.filter(user__created_at__gte=hace_6_meses)
            .annotate(mes=TruncMonth('user__created_at'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        nombres_mes = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                       'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        labels = [nombres_mes[d['mes'].month - 1] for d in data]
        counts = [d['total'] for d in data]
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Nuevos pacientes',
                'data': counts,
                'borderColor': '#0d6efd',
                'backgroundColor': 'rgba(13, 110, 253, 0.15)',
                'fill': True,
                'tension': 0.4,
            }],
        })


class CitasPorEstadoView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        estados = [
            ('PENDIENTE', 'Pendiente', '#ffc107'),
            ('CONFIRMADA', 'Confirmada', '#198754'),
            ('CANCELADA', 'Cancelada', '#dc3545'),
            ('COMPLETADA', 'Completada', '#0d6efd'),
        ]
        return JsonResponse({
            'labels': [e[1] for e in estados],
            'datasets': [{
                'data': [Cita.objects.filter(estado=e[0]).count() for e in estados],
                'backgroundColor': [e[2] for e in estados],
                'borderWidth': 2,
                'borderColor': '#fff',
            }],
        })


class CitasPorDiaView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # ExtractIsoWeekDay: 1=Lunes … 7=Domingo
        data = (
            Cita.objects.annotate(dia=ExtractIsoWeekDay('fecha_hora'))
            .values('dia')
            .annotate(total=Count('id'))
            .order_by('dia')
        )
        dias = {1: 'Lun', 2: 'Mar', 3: 'Mié', 4: 'Jue', 5: 'Vie', 6: 'Sáb', 7: 'Dom'}
        counts_by_day = {d['dia']: d['total'] for d in data}
        return JsonResponse({
            'labels': list(dias.values()),
            'datasets': [{
                'label': 'Citas',
                'data': [counts_by_day.get(i, 0) for i in range(1, 8)],
                'backgroundColor': '#0dcaf0',
                'borderColor': '#0aa2c0',
                'borderWidth': 1,
            }],
        })
