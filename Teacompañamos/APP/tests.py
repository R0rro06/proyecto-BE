from django.test import TestCase
from django.urls import reverse

from .models import Leccion, Modulo, Progreso


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

    def test_respuesta_correcta_muestra_explicacion_sin_guardar_progreso(self):
        response = self.client.post(
            reverse('responder_leccion', args=[self.leccion.pk]),
            {'respuesta': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¡Correcto!')
        self.assertContains(response, self.leccion.explicacion)
        self.assertEqual(Progreso.objects.count(), 0)
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
        self.assertEqual(Progreso.objects.count(), 0)

    def test_respuesta_ausente_muestra_error_y_no_guarda_progreso(self):
        response = self.client.post(
            reverse('responder_leccion', args=[self.leccion.pk]),
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Este campo es obligatorio.', status_code=400)
        self.assertEqual(Progreso.objects.count(), 0)
