from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class MixinPermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_user',
            password='testpass123',
            role=User.ADMIN,
        )
        self.medico = User.objects.create_user(
            username='medico_user',
            password='testpass123',
            role=User.MEDICO,
        )
        self.paciente = User.objects.create_user(
            username='paciente_user',
            password='testpass123',
            role=User.PACIENTE,
        )
        self.user_list_url = reverse('users:user_list')

    def _toggle_url(self, pk):
        return reverse('users:user_toggle', args=[pk])

    # ── Acceso a UserListView ──────────────────────────────────────────────────

    def test_admin_can_access_user_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 200)

    def test_medico_cannot_access_user_list(self):
        self.client.force_login(self.medico)
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 302)

    def test_paciente_cannot_access_user_list(self):
        self.client.force_login(self.paciente)
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    # ── UserToggleActiveView ───────────────────────────────────────────────────

    def test_admin_can_toggle_user(self):
        self.client.force_login(self.admin)
        url = self._toggle_url(self.paciente.pk)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        # is_active se invirtió (por defecto era True → ahora False)
        self.paciente.refresh_from_db()
        self.assertFalse(self.paciente.is_active)

    def test_toggle_is_reversible(self):
        self.client.force_login(self.admin)
        url = self._toggle_url(self.paciente.pk)
        self.client.post(url)  # desactiva
        self.client.post(url)  # reactiva
        self.paciente.refresh_from_db()
        self.assertTrue(self.paciente.is_active)

    def test_admin_cannot_deactivate_himself(self):
        self.client.force_login(self.admin)
        url = self._toggle_url(self.admin.pk)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        # El admin sigue activo
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_non_admin_cannot_toggle(self):
        self.client.force_login(self.medico)
        url = self._toggle_url(self.paciente.pk)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
