from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Permission, User
from django.db import IntegrityError
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.urls import reverse

from .models import Leccion, Modulo, Perfil, Progreso, Rol, Usuario
from .student_session import STUDENT_ID_KEY


class SesionesYProgresoTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            username='estudiante', email='estudiante@example.com',
            password=make_password('Clave-Estudiante-2026!'),
        )
        self.modulo = Modulo.objects.create(
            titulo='Inicio', descripcion='Módulo inicial', orden=1,
        )
        self.leccion = Leccion.objects.create(
            pregunta='¿Es verdadero?', es_verdad=1,
            explicacion='Sí.', modulo=self.modulo,
        )

    def ingresar(self):
        return self.client.post(reverse('acceso_estudiante'), {
            'username': 'estudiante', 'password': 'Clave-Estudiante-2026!',
        })

    def test_login_verifica_clave_y_crea_perfil_de_estudiante(self):
        incorrecto = self.client.post(reverse('acceso_estudiante'), {
            'username': 'estudiante', 'password': 'otra-clave',
        })
        self.assertEqual(incorrecto.status_code, 200)
        self.assertContains(incorrecto, 'Usuario o contraseña incorrectos.')
        self.assertNotIn(STUDENT_ID_KEY, self.client.session)
        self.assertEqual(Perfil.objects.count(), 0)

        correcto = self.ingresar()
        self.assertRedirects(correcto, reverse('dashboard'))
        self.assertTrue(correcto.cookies['sessionid']['expires'])
        self.assertEqual(self.client.session[STUDENT_ID_KEY], self.usuario.pk)
        self.assertTrue(Session.objects.filter(
            session_key=self.client.session.session_key,
        ).exists())
        self.assertEqual(
            Perfil.objects.get(usuario=self.usuario).rol.nombre, 'Estudiante',
        )
        dashboard = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard, '¡Hola, estudiante!')
        self.assertContains(dashboard, '0 de 1 lecciones')

    def test_base_de_datos_impide_usuarios_duplicados(self):
        with self.assertRaises(IntegrityError):
            Usuario.objects.create(
                username='ESTUDIANTE', email='otro@example.com',
                password=make_password('Clave-Estudiante-2026!'),
            )

    def test_respuestas_guardan_intentos_y_avance_solo_para_su_perfil(self):
        self.ingresar()
        url = reverse('responder_leccion', args=[self.leccion.pk])
        self.client.post(url, {'respuesta': '0'})
        progreso = Progreso.objects.get()
        self.assertEqual(progreso.intentos, 1)
        self.assertIsNone(progreso.fecha_completada)

        self.client.post(url, {'respuesta': '1'})
        progreso.refresh_from_db()
        self.assertEqual(progreso.intentos, 2)
        self.assertIsNotNone(progreso.fecha_completada)
        self.assertContains(self.client.get(reverse('dashboard')), '1 de 1 lecciones')

        self.client.post(url, {'respuesta': '1'})
        progreso.refresh_from_db()
        self.assertEqual(progreso.intentos, 3)
        self.assertEqual(Progreso.objects.count(), 1)

        otro = Usuario.objects.create(
            username='otro', email='otro@example.com', password=make_password('Clave-Otro-2026!'),
        )
        self.client.post(reverse('salir_estudiante'))
        self.client.post(reverse('acceso_estudiante'), {
            'username': otro.username, 'password': 'Clave-Otro-2026!',
        })
        self.assertContains(self.client.get(reverse('dashboard')), '0 de 1 lecciones')
        self.assertEqual(Progreso.objects.count(), 1)
        self.leccion.refresh_from_db()
        self.assertEqual(self.leccion.completada, 0)

    def test_renombrar_rol_no_pierde_el_avance(self):
        self.ingresar()
        self.client.post(
            reverse('responder_leccion', args=[self.leccion.pk]),
            {'respuesta': '1'},
        )
        perfil = Perfil.objects.get(usuario=self.usuario)
        perfil.rol.nombre = 'Alumno'
        perfil.rol.save(update_fields=('nombre',))

        self.assertContains(self.client.get(reverse('dashboard')), '1 de 1 lecciones')
        self.assertEqual(Perfil.objects.count(), 1)
        self.assertEqual(Rol.objects.count(), 5)

        self.client.post(reverse('salir_estudiante'))
        self.ingresar()
        self.assertContains(self.client.get(reverse('dashboard')), '1 de 1 lecciones')
        self.assertEqual(Perfil.objects.count(), 1)

    def test_respuesta_anonima_o_invalida_no_guarda_avance(self):
        url = reverse('responder_leccion', args=[self.leccion.pk])
        self.client.post(url, {'respuesta': '1'})
        self.assertEqual(Progreso.objects.count(), 0)
        self.ingresar()
        response = self.client.post(url, {'respuesta': 'no-valida'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Progreso.objects.count(), 0)

    def test_cambiar_clave_invalida_sesion_y_salir_exige_post(self):
        self.ingresar()
        self.usuario.password = make_password('Clave-Nueva-2026!')
        self.usuario.save(update_fields=('password',))
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('inicio') + '?next=%2Fdashboard%2F', fetch_redirect_response=False)
        self.assertNotIn(STUDENT_ID_KEY, self.client.session)

        self.usuario.password = make_password('Clave-Estudiante-2026!')
        self.usuario.save(update_fields=('password',))
        self.ingresar()
        self.assertEqual(self.client.get(reverse('salir_estudiante')).status_code, 405)
        self.assertRedirects(
            self.client.post(reverse('salir_estudiante')), reverse('inicio'),
        )
        self.assertNotIn(STUDENT_ID_KEY, self.client.session)

    def test_cookie_lectura_se_aplica_y_se_borra(self):
        self.ingresar()
        response = self.client.post(reverse('preferencia_lectura'), {
            'lectura_ampliada': '1', 'next': reverse('aprender_modulo', args=[self.modulo.pk]),
        })
        self.assertRedirects(
            response, reverse('aprender_modulo', args=[self.modulo.pk]),
        )
        cookie = response.cookies['lectura_ampliada']
        self.assertEqual(cookie.value, '1')
        self.assertEqual(cookie['max-age'], 30 * 24 * 60 * 60)
        self.assertTrue(cookie['httponly'])
        self.assertContains(
            self.client.get(reverse('aprender_modulo', args=[self.modulo.pk])),
            'class="reading-large"',
        )

        response = self.client.post(reverse('preferencia_lectura'), {
            'lectura_ampliada': '0', 'next': 'https://otro-sitio.example/',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(response.cookies['lectura_ampliada']['max-age'], 0)
        self.assertNotContains(self.client.get(reverse('dashboard')), 'class="reading-large"')

    def test_cookie_manipulada_y_csrf(self):
        self.client.cookies['lectura_ampliada'] = 'valor-no-valido'
        self.assertNotContains(self.client.get(reverse('inicio')), 'class="reading-large"')
        self.assertEqual(self.client.get(reverse('preferencia_lectura')).status_code, 405)
        strict_client = Client(enforce_csrf_checks=True)
        self.assertEqual(
            strict_client.post(reverse('preferencia_lectura'), {'lectura_ampliada': '1'}).status_code,
            403,
        )

class PanelContentPermissionsTests(TestCase):
    def test_solo_admin_autorizado_puede_ver_y_modificar_contenido(self):
        panel = reverse('panel_administracion')
        create = reverse('cursos_modulo_form')
        self.assertEqual(self.client.get(panel).status_code, 302)
        self.assertEqual(self.client.post(create, {
            'titulo': 'Sin permiso', 'descripcion': 'No', 'orden': 1,
        }).status_code, 302)
        self.assertFalse(Modulo.objects.exists())

        staff = User.objects.create_user(
            username='personal', password='Clave-Personal-2026!', is_staff=True,
        )
        self.client.force_login(staff)
        self.assertEqual(self.client.get(panel).status_code, 403)
        self.assertEqual(self.client.post(create, {
            'titulo': 'Sin permiso', 'descripcion': 'No', 'orden': 1,
        }).status_code, 403)

        permissions = Permission.objects.filter(
            content_type__app_label='APP', codename__in=('view_modulo', 'add_modulo'),
        )
        staff.user_permissions.add(*permissions)
        self.assertEqual(self.client.get(panel).status_code, 403)
        response = self.client.post(create, {
            'titulo': 'Con permiso', 'descripcion': 'Sí', 'orden': 1,
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Modulo.objects.filter(titulo='Con permiso').exists())
