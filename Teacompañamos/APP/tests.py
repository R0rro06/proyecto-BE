from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from .models import Leccion, Modulo, Progreso, Usuario


class FlujoDeAprendizajeTests(TestCase):
    def setUp(self):
        self.modulo = Modulo.objects.create(
            titulo='Módulo de prueba',
            descripcion='Descripción del módulo',
            orden=1,
        )
        self.leccion = Leccion.objects.create(
            pregunta='¿La Tierra gira alrededor del Sol?',
            es_verdad=1,
            explicacion='La Tierra gira alrededor del Sol.',
            modulo=self.modulo,
        )
        account = User.objects.create_user(
            username='alumno', email='alumno@example.com', password='Clave-Alumno-2026!',
        )
        self.usuario = Usuario.objects.create(
            username='alumno', email='alumno@example.com', password=make_password(None),
            django_user=account,
        )
        self.client.post(reverse('acceso_estudiante'), {
            'username': 'alumno', 'password': 'Clave-Alumno-2026!',
        })

    def test_dashboard_enlaza_al_modulo(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('aprender_modulo', args=[self.modulo.pk]))
        self.assertContains(response, self.modulo.titulo)

    def test_modulo_muestra_enlace_a_sus_lecciones(self):
        response = self.client.get(reverse('aprender_modulo', args=[self.modulo.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.leccion.pregunta)
        self.assertContains(response, reverse('responder_leccion', args=[self.leccion.pk]))

    def test_respuesta_correcta_muestra_explicacion_y_guarda_progreso(self):
        response = self.client.post(
            reverse('responder_leccion', args=[self.leccion.pk]),
            {'respuesta': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¡Correcto!')
        self.assertContains(response, self.leccion.explicacion)
        self.assertEqual(Progreso.objects.count(), 1)
        self.leccion.refresh_from_db()
        self.assertEqual(self.leccion.completada, 0)

    def test_respuesta_incorrecta_muestra_respuesta_correcta(self):
        response = self.client.post(
            reverse('responder_leccion', args=[self.leccion.pk]),
            {'respuesta': '0'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Respuesta incorrecta')
        self.assertContains(response, 'La respuesta correcta es <strong>Verdadero.')
        self.assertEqual(Progreso.objects.count(), 1)

    def test_respuesta_ausente_muestra_error_y_no_guarda_progreso(self):
        response = self.client.post(
            reverse('responder_leccion', args=[self.leccion.pk]),
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Este campo es obligatorio.', status_code=400)
        self.assertEqual(Progreso.objects.count(), 0)
