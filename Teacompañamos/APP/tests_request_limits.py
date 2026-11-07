from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Rol


class FormBodyLimitTests(TestCase):
    def test_large_public_form_is_rejected_before_parsing(self):
        response = self.client.post(reverse('acceso_estudiante'), {
            'username': 'x' * (256 * 1024), 'password': 'irrelevant',
        })
        self.assertEqual(response.status_code, 413)

    def test_normal_public_form_still_reaches_validation(self):
        response = self.client.post(reverse('acceso_estudiante'), {
            'username': 'unknown', 'password': 'incorrect',
        })
        self.assertEqual(response.status_code, 200)

    def test_absurd_content_length_is_rejected_without_parsing(self):
        response = self.client.generic('POST', reverse('acceso_estudiante'), b'',
                                       CONTENT_LENGTH='9' * 5000)
        self.assertEqual(response.status_code, 413)


class SecurityRegressionTests(TestCase):
    def test_normalized_admin_name_is_reserved_at_registration(self):
        response = self.client.post(reverse('registro_usuario'), {
            'username': 'ａｄｍｉｎ', 'email': 'new@example.com',
            'password1': 'Clave-Larga-2026!', 'password2': 'Clave-Larga-2026!',
            'tipo': 'estudiante',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'reservado')
        self.assertFalse(get_user_model().objects.filter(username='admin').exists())

    def test_http_delete_cannot_bypass_role_deletion_guard(self):
        admin = get_user_model().objects.create_superuser(
            'admin', 'admin@example.com', 'Clave-Admin-2026!',
        )
        self.client.force_login(admin)
        rol = Rol.objects.create(nombre='Temporal')
        response = self.client.delete(reverse('rol_delete', args=[rol.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Rol.objects.filter(pk=rol.pk).exists())

    def test_theme_preference_rejects_unsafe_location_header(self):
        response = self.client.post(reverse('preferencia_tema'), {
            'next': '/dashboard/\r\nX-Forged: yes', 'tema': 'oscuro',
        })
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('\r', response['Location'])
        self.assertNotIn('\n', response['Location'])
