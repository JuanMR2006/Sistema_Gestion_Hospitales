import logging

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView

from .forms import AdminUserForm, LoginForm, ProfileForm, RegisterForm, UserUpdateForm
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
                if user.is_medico:
                    from medical.models import Medico
                    Medico.objects.create(
                        user=user,
                        especialidad=form.cleaned_data['especialidad'],
                        numero_licencia=form.cleaned_data['numero_licencia'],
                    )
                elif user.is_paciente:
                    from medical.models import HistoriaClinica, Paciente
                    paciente = Paciente.objects.create(
                        user=user,
                        fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                        genero=form.cleaned_data['genero'],
                        blood_type=form.cleaned_data.get('blood_type') or '',
                    )
                    HistoriaClinica.objects.create(paciente=paciente)
                login(request, user)
                display = user.get_full_name().strip() or user.username
                messages.success(request, f'¡Bienvenido/a, {display}! Tu cuenta fue creada exitosamente.')
                return _redirect_by_role(user)
            except IntegrityError:
                logger.exception('IntegrityError al crear usuario en RegisterView')
                messages.error(request, 'Ocurrió un error al crear la cuenta. Intenta nuevamente.')
        return render(request, self.template_name, {'form': form})


class ProfileView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'

    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect(reverse('users:profile'))
        return render(request, self.template_name, {'form': form})


# ── Vistas de gestión de usuarios (solo admin) ────────────────────────────────

class UserListView(AdminRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        qs = get_user_model().objects.all().order_by('last_name', 'first_name')
        role = self.request.GET.get('role', '').strip()
        is_active = self.request.GET.get('is_active', '').strip()
        q = self.request.GET.get('q', '').strip()
        if role:
            qs = qs.filter(role=role)
        if is_active in ('true', 'false'):
            qs = qs.filter(is_active=(is_active == 'true'))
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(username__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roles'] = get_user_model().ROLE_CHOICES
        ctx['current_filters'] = {
            'role': self.request.GET.get('role', ''),
            'is_active': self.request.GET.get('is_active', ''),
            'q': self.request.GET.get('q', ''),
        }
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['filter_query_string'] = params.urlencode()
        return ctx


class UserUpdateView(AdminRequiredMixin, View):
    template_name = 'users/user_form.html'

    def _get_user(self, pk):
        return get_object_or_404(get_user_model(), pk=pk)

    def get(self, request, pk):
        target_user = self._get_user(pk)
        form = AdminUserForm(instance=target_user)
        return render(request, self.template_name, {'form': form, 'target_user': target_user})

    def post(self, request, pk):
        target_user = self._get_user(pk)
        if target_user.pk == request.user.pk and 'is_active' not in request.POST:
            messages.error(request, 'No puedes desactivar tu propia cuenta.')
            form = AdminUserForm(request.POST, instance=target_user)
            return render(request, self.template_name, {'form': form, 'target_user': target_user})
        form = AdminUserForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario "{target_user.username}" actualizado correctamente.')
            return redirect(reverse('users:user_list'))
        return render(request, self.template_name, {'form': form, 'target_user': target_user})


class UserInfoView(AdminRequiredMixin, View):
    def get(self, request, pk):
        User = get_user_model()
        try:
            user = User.objects.get(pk=pk)
            return JsonResponse({
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'username': user.username,
            })
        except User.DoesNotExist:
            return JsonResponse({}, status=404)


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
