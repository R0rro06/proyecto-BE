from django.test import SimpleTestCase, Client, RequestFactory
from django.template.loader import render_to_string
from django.http import HttpResponse
from .cookie_consent import CookieConsentMiddleware
from django.urls import reverse


class CookieConsentTests(SimpleTestCase):
    def test_aviso_aparece_solo_hasta_elegir_y_boton_lateral_sigue_disponible(self):
        for choice in ('aceptar', 'rechazar'):
            with self.subTest(choice=choice):
                client = Client()
                initial = client.get(reverse('inicio'))
                self.assertRegex(initial.content.decode(), r'<details\s+open>')
                self.assertContains(initial, 'Abrir o cerrar preferencias de cookies')
                client.post(reverse('consentimiento_cookies'), {'consentimiento': choice})
                revisit = client.get(reverse('inicio'))
                self.assertNotRegex(revisit.content.decode(), r'<details\s+open>')
                self.assertContains(revisit, 'Abrir o cerrar preferencias de cookies')

    def test_saved_theme_is_rendered_and_ignored_without_consent(self):
        for consent in ('aceptar', 'rechazar'):
            with self.subTest(consent=consent):
                request = RequestFactory().get('/')
                request.COOKIES = {'consentimiento_cookies': consent, 'tema': 'oscuro'}
                def render_page(request):
                    return HttpResponse(render_to_string('APP/learning/inicio.html', request=request))
                response = CookieConsentMiddleware(render_page)(request)
                self.assertContains(response, 'data-tema="%s"' % ('oscuro' if consent == 'aceptar' else 'claro'))
                self.assertContains(response, 'Modo oscuro')

    def test_theme_saved_only_with_consent(self):
        for consent in (None, 'rechazar', 'aceptar'):
            with self.subTest(consent=consent):
                client = Client()
                if consent:
                    client.cookies['consentimiento_cookies'] = consent
                response = client.post(reverse('preferencia_tema'), {
                    'tema': 'oscuro', 'next': '/acceso/',
                })
                self.assertRedirects(response, '/acceso/', fetch_redirect_response=False)
                if consent == 'aceptar':
                    self.assertEqual(response.cookies['tema'].value, 'oscuro')
                    self.assertEqual(response.cookies['tema']['max-age'], 180 * 24 * 60 * 60)
                else:
                    self.assertEqual(response.cookies['tema']['max-age'], 0)

    def test_theme_validation_and_csrf(self):
        url = reverse('preferencia_tema')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {'tema': 'invalid'}).status_code, 400)
        self.assertEqual(Client(enforce_csrf_checks=True).post(url, {'tema': 'oscuro'}).status_code, 403)

    def test_theme_rejection_removes_saved_theme(self):
        self.client.cookies['consentimiento_cookies'] = 'aceptar'
        self.client.cookies['tema'] = 'oscuro'
        response = self.client.post(reverse('consentimiento_cookies'), {'consentimiento': 'rechazar'})
        self.assertEqual(response.cookies['tema']['max-age'], 0)

    def test_accept_remembers_choice_and_returns_to_page(self):
        response = self.client.post(reverse('consentimiento_cookies'), {
            'consentimiento': 'aceptar', 'next': '/acceso/',
        })
        self.assertRedirects(response, '/acceso/', fetch_redirect_response=False)
        cookie = response.cookies['consentimiento_cookies']
        self.assertEqual(cookie.value, 'aceptar')
        self.assertEqual(cookie['max-age'], 180 * 24 * 60 * 60)
        self.assertTrue(cookie['httponly'])

    def test_reject_clears_optional_cookie_and_blocks_external_redirect(self):
        self.client.cookies['consentimiento_cookies'] = 'aceptar'
        self.client.cookies['tema'] = 'oscuro'
        response = self.client.post(reverse('consentimiento_cookies'), {
            'consentimiento': 'rechazar', 'next': 'https://example.org/',
        })
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(response.cookies['consentimiento_cookies'].value, 'rechazar')
        self.assertEqual(response.cookies['tema']['max-age'], 0)

    def test_consent_requires_valid_post_and_csrf(self):
        url = reverse('consentimiento_cookies')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {'consentimiento': 'otro'}).status_code, 400)
        self.assertEqual(Client(enforce_csrf_checks=True).post(
            url, {'consentimiento': 'aceptar'},
        ).status_code, 403)
