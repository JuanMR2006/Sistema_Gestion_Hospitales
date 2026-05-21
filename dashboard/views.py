# dashboard/views.py
import logging
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from appointments.models import Cita
from medical.models import Especialidad, Medico, Paciente
from users.mixins import (
    AdminOrMedicoMixin,
    AdminRequiredMixin,
    MedicoRequiredMixin,
    PacienteRequiredMixin,
)
from users.models import CustomUser

from .forms import AdminPanelFilterForm

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


# ── Panel Admin ────────────────────────────────────────────────────────────

class AdminPanelView(AdminRequiredMixin, View):
    template_name = 'dashboard/admin_panel.html'

    def get(self, request, *args, **kwargs):
        form = AdminPanelFilterForm(request.GET or None)

        citas = Cita.objects.select_related(
            'paciente__user', 'medico__user', 'medico__especialidad'
        ).order_by('-fecha_hora')

        hay_filtros = False

        if form.is_valid():
            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')
            especialidad = form.cleaned_data.get('especialidad')
            estado = form.cleaned_data.get('estado')
            medico = form.cleaned_data.get('medico')

            if fecha_inicio:
                citas = citas.filter(fecha_hora__date__gte=fecha_inicio)
                hay_filtros = True
            if fecha_fin:
                citas = citas.filter(fecha_hora__date__lte=fecha_fin)
                hay_filtros = True
            if especialidad:
                citas = citas.filter(medico__especialidad=especialidad)
                hay_filtros = True
            if estado:
                citas = citas.filter(estado=estado)
                hay_filtros = True
            if medico:
                citas = citas.filter(medico=medico)
                hay_filtros = True

        total_resultados = citas.count()
        paginator = Paginator(citas, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        query_params = request.GET.copy()
        query_params.pop('page', None)

        return render(request, self.template_name, {
            'form': form,
            'page_obj': page_obj,
            'total_resultados': total_resultados,
            'medicos_lista': Medico.objects.select_related('user', 'especialidad'),
            'especialidades_lista': Especialidad.objects.filter(activa=True),
            'hay_filtros': hay_filtros,
            'query_string': query_params.urlencode(),
        })


# ── Buscador de pacientes ──────────────────────────────────────────────────

class SearchPacienteView(AdminOrMedicoMixin, View):
    template_name = 'dashboard/search_results.html'

    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        resultados = []

        if len(q) >= 2:
            usuarios = (
                CustomUser.objects
                .filter(role=CustomUser.PACIENTE)
                .filter(
                    Q(first_name__icontains=q)
                    | Q(last_name__icontains=q)
                    | Q(email__icontains=q)
                    | Q(phone__icontains=q)
                )
                .select_related('paciente_profile')[:20]
            )

            for user in usuarios:
                if not hasattr(user, 'paciente_profile'):
                    logger.warning('Usuario %s con rol PACIENTE sin perfil', user.pk)
                    continue
                paciente = user.paciente_profile
                ultima = (
                    Cita.objects
                    .filter(paciente=paciente)
                    .order_by('-fecha_hora')
                    .first()
                )
                resultados.append({
                    'id': paciente.pk,
                    'nombre': user.get_full_name(),
                    'email': user.email,
                    'telefono': user.phone or '',
                    'ultima_cita': (
                        ultima.fecha_hora.strftime('%d/%m/%Y')
                        if ultima else 'Sin citas'
                    ),
                    'url_detalle': reverse(
                        'medical:patient_detail', args=[paciente.pk]
                    ),
                })

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(resultados, safe=False)

        return render(request, self.template_name, {
            'q': q,
            'resultados': resultados,
            'total': len(resultados),
        })
