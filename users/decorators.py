from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def _login_redirect():
    return redirect(reverse('users:login'))


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _login_redirect()
        if not request.user.is_admin:
            messages.error(request, 'Necesitas permisos de administrador para acceder a esta página.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


def medico_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _login_redirect()
        if not request.user.is_medico:
            messages.error(request, 'Esta sección es exclusiva para médicos.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


def paciente_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _login_redirect()
        if not request.user.is_paciente:
            messages.error(request, 'Esta sección es exclusiva para pacientes.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_medico_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _login_redirect()
        if not (request.user.is_admin or request.user.is_medico):
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper
