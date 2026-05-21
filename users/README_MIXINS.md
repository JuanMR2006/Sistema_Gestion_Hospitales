# Mixins y Decoradores de Permisos — App `users`

## Tabla de referencia rápida

| Situación | Mixin (CBV) | Decorador (FBV) | Comportamiento si falla |
|-----------|-------------|-----------------|-------------------------|
| Solo administradores | `AdminRequiredMixin` | `@admin_required` | Redirige a `/` con `messages.error` |
| Solo médicos | `MedicoRequiredMixin` | `@medico_required` | Redirige a `/` con `messages.error` |
| Solo pacientes | `PacienteRequiredMixin` | `@paciente_required` | Redirige a `/` con `messages.error` |
| Admin o médico | `AdminOrMedicoMixin` | `@admin_or_medico_required` | Redirige a `/` con `messages.error` |
| Redirección por rol | `RoleRedirectMixin` | — | N/A (helper, no bloquea) |

> **Regla común:** si el usuario **no está autenticado** → redirige a `users:login`.  
> Si está autenticado pero **no tiene el rol correcto** → mensaje de error + redirige al inicio.  
> Nunca se lanza un 403.

---

## Ejemplo: Vista basada en clase (CBV)

```python
# appointments/views.py
from users.mixins import AdminOrMedicoMixin
from django.views.generic import ListView
from .models import Cita

class CitaListView(AdminOrMedicoMixin, ListView):
    model = Cita
    template_name = 'appointments/cita_list.html'
    context_object_name = 'citas'
```

El mixin **siempre va primero** en la lista de herencia, antes de la clase genérica de Django.

---

## Ejemplo: Vista de función (FBV) con decorador

```python
# appointments/views.py
from users.decorators import medico_required
from django.shortcuts import render

@medico_required
def mis_pacientes(request):
    return render(request, 'appointments/mis_pacientes.html')
```

---

## RoleRedirectMixin — redirección por rol

Útil en vistas de login o dashboard que deben enviar al usuario a su área correcta:

```python
# users/views.py
from users.mixins import RoleRedirectMixin
from django.views import View

class DashboardDispatchView(RoleRedirectMixin, View):
    def get(self, request):
        return redirect(self.get_redirect_url_by_role(request.user))
```

| Rol | URL de destino |
|-----|----------------|
| `ADMIN` | `dashboard:admin_dashboard` |
| `MEDICO` | `appointments:cita_list` |
| `PACIENTE` | `appointments:mis_citas` |

Si el nombre de URL aún no existe, cae en rutas hardcodeadas como fallback automático.

---

## URLs protegidas actualmente

| URL | Vista | Mixin aplicado |
|-----|-------|----------------|
| `GET /users/` | `UserListView` | `AdminRequiredMixin` |
| `GET /users/<pk>/edit/` | `UserUpdateView` | `AdminRequiredMixin` |
| `POST /users/<pk>/toggle/` | `UserToggleActiveView` | `AdminRequiredMixin` |

---

## Ejecutar los tests

```bash
python manage.py test users
```

Los tests cubren:
- Admin accede a lista de usuarios → 200
- Médico/paciente no acceden → 302
- Anónimo redirige a login
- Admin activa/desactiva otro usuario → JsonResponse `success: true`
- Toggle es reversible
- Admin no puede modificar su propia cuenta → `success: false`
- No-admin no puede hacer toggle → 302
