import logging

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, UpdateView

from .forms import LoginForm, RegisterForm, UserUpdateForm
from .mixins import AdminRequiredMixin

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


# ── Vistas de gestión de usuarios (solo admin) ────────────────────────────────

class UserListView(AdminRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    ordering = ['last_name', 'first_name']


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = 'users/user_update.html'
    success_url = reverse_lazy('users:user_list')


class UserToggleActiveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        if pk == request.user.pk:
            return JsonResponse({'success': False, 'error': 'No puedes modificar tu propia cuenta.'})
        User = get_user_model()
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Usuario no encontrado.'})
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        estado = 'activado' if user.is_active else 'desactivado'
        return JsonResponse({'success': True, 'is_active': user.is_active, 'message': f'Usuario {estado} correctamente.'})
