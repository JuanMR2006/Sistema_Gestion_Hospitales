import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views import View

from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)


def _redirect_by_role(user):
    if user.is_admin:
        return redirect('/dashboard/')
    if user.is_medico:
        return redirect('/appointments/')
    return redirect('/appointments/my/')


class CustomLoginView(View):
    template_name = 'users/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return _redirect_by_role(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return _redirect_by_role(user)
            messages.error(request, 'Usuario o contraseña incorrectos.')
        return render(request, self.template_name, {'form': form})


class CustomLogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, 'Sesión cerrada correctamente.')
        return redirect('/users/login/')


class RegisterView(View):
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return _redirect_by_role(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                display = user.get_full_name().strip() or user.username
                messages.success(request, f'¡Bienvenido/a, {display}! Tu cuenta fue creada exitosamente.')
                return redirect('/appointments/my/')
            except IntegrityError:
                logger.exception('IntegrityError al crear usuario en RegisterView')
                messages.error(request, 'Ocurrió un error al crear la cuenta. Intenta nuevamente.')
        return render(request, self.template_name, {'form': form})
