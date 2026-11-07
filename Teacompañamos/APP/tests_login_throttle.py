from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .login_throttle import attempt_key
from .models import LoginAttempt, Usuario


class LoginThrottleTests(TestCase):
    def test_sitio_bloquea_tras_cinco_fallos_y_permite_entrar_tras_un_minuto(self):
        account = User.objects.create_user('alumno', password='Clave-Alumno-2026!')
        Usuario.objects.create(username='alumno', password='!', django_user=account)
        url = reverse('acceso_estudiante')
        for _ in range(4):
            response = self.client.post(url, {'username': 'alumno', 'password': 'incorrecta'})
            self.assertEqual(response.status_code, 200)
        response = self.client.post(url, {'username': 'alumno', 'password': 'incorrecta'})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '60')
        self.assertContains(response, 'Demasiados intentos', status_code=429)

        response = self.client.post(url, {'username': 'alumno', 'password': 'Clave-Alumno-2026!'})
        self.assertEqual(response.status_code, 429)
        key = attempt_key(response.wsgi_request, 'alumno')
        LoginAttempt.objects.filter(pk=key).update(blocked_until=timezone.now() - timedelta(seconds=1))
        response = self.client.post(url, {'username': 'alumno', 'password': 'Clave-Alumno-2026!'})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(LoginAttempt.objects.filter(pk=key).exists())

    def test_admin_comparte_bloqueo_entre_acceso_y_django_admin(self):
        User.objects.create_superuser('admin', password='Clave-Admin-2026!')
        public_url = reverse('acceso_estudiante')
        admin_url = reverse('admin:login')
        for _ in range(4):
            response = self.client.post(public_url, {
                'username': 'admin', 'password': 'incorrecta', 'tipo': 'administrador',
            })
            self.assertEqual(response.status_code, 200)
        response = self.client.post(admin_url, {'username': 'admin', 'password': 'incorrecta'})
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, 'Demasiados intentos', status_code=429)
        self.assertEqual(self.client.post(admin_url, {
            'username': 'admin', 'password': 'Clave-Admin-2026!',
        }).status_code, 429)
        self.assertEqual(self.client.post(public_url, {
            'username': 'admin', 'password': 'Clave-Admin-2026!', 'tipo': 'administrador',
        }).status_code, 429)
        key = attempt_key(response.wsgi_request, 'admin', admin=True)
        LoginAttempt.objects.filter(pk=key).update(blocked_until=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.post(admin_url, {
            'username': 'admin', 'password': 'Clave-Admin-2026!',
        }).status_code, 302)
        self.assertFalse(LoginAttempt.objects.filter(pk=key).exists())
