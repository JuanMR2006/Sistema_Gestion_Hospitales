import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse

logger = logging.getLogger(__name__)


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = False

    def test_func(self):
        return self.request.user.is_admin

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('users:login'))
        messages.error(self.request, 'Necesitas permisos de administrador para acceder a esta página.')
        return redirect('/')


class MedicoRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = False

    def test_func(self):
        return self.request.user.is_medico

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('users:login'))
        messages.error(self.request, 'Esta sección es exclusiva para médicos.')
        return redirect('/')


class PacienteRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = False

    def test_func(self):
        return self.request.user.is_paciente

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('users:login'))
        messages.error(self.request, 'Esta sección es exclusiva para pacientes.')
        return redirect('/')


class AdminOrMedicoMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = False

    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_medico

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('users:login'))
        messages.error(self.request, 'No tienes permiso para acceder a esta sección.')
        return redirect('/')


class RoleRedirectMixin:
    """Provee get_redirect_url_by_role() para redirigir según el rol del usuario."""

    def get_redirect_url_by_role(self, user):
        try:
            if user.is_admin:
                return reverse('dashboard:admin_dashboard')
            if user.is_medico:
                return reverse('appointments:cita_list')
            return reverse('appointments:mis_citas')
        except NoReverseMatch:
            # Fallback mientras las apps aún no tienen sus URLs configuradas
            if user.is_admin:
                return '/dashboard/'
            if user.is_medico:
                return '/appointments/'
            return '/appointments/my/'
