from django.contrib import admin as django_admin
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Leccion, Modulo, Perfil, Rol, Usuario
from .student_session import STUDENT_ID_KEY


class AccesoYRegistroTests(TestCase):
    def test_inicio_antes_del_dashboard_y_proteccion_de_lecciones(self):
        modulo = Modulo.objects.create(titulo='Inicio', descripcion='Contenido', orden=1)
        leccion = Leccion.objects.create(
            pregunta='¿Es verdadero?', es_verdad=1, explicacion='Sí', modulo=modulo,
        )
        inicio = self.client.get(reverse('inicio'))
        self.assertContains(inicio, 'Estudiante')
        self.assertContains(inicio, 'Familiar')
        self.assertContains(inicio, 'Profesor')
        self.assertContains(inicio, 'Otro')
        self.assertContains(inicio, 'Ingresar como administrador')
        for url in (reverse('dashboard'), reverse('aprender_modulo', args=[modulo.pk]),
                    reverse('responder_leccion', args=[leccion.pk])):
            self.assertEqual(self.client.get(url).status_code, 302)
            self.assertEqual(self.client.post(url, {'respuesta': '1'}).status_code, 302)

    def test_registro_crea_usuario_perfil_y_sesion_para_cada_tipo(self):
        for codigo in ('estudiante', 'familiar', 'profesor', 'otro'):
            self.client.post(reverse('salir_estudiante'))
            response = self.client.post(reverse('registro_usuario'), {
                'username': codigo, 'email': f'{codigo}@example.com',
                'password1': 'Clave-Registro-2026!',
                'password2': 'Clave-Registro-2026!', 'tipo': codigo,
            })
            self.assertRedirects(response, reverse('dashboard'))
            usuario = Usuario.objects.get(username=codigo)
            self.assertTrue(check_password('Clave-Registro-2026!', usuario.password))
            self.assertEqual(Perfil.objects.get(usuario=usuario).rol.codigo, codigo)
            self.assertEqual(self.client.session[STUDENT_ID_KEY], usuario.pk)
            self.assertFalse(User.objects.filter(username=codigo).exists())
            self.assertRedirects(self.client.get(reverse('inicio')), reverse('dashboard'))

    def test_registro_rechaza_duplicados_y_roles_invalidos(self):
        Usuario.objects.create(username='Alumno', email='alumno@example.com', password='hash')
        for username, email, tipo in (
            ('ALUMNO', 'nuevo@example.com', 'estudiante'),
            ('nuevo', 'ALUMNO@example.com', 'estudiante'),
            ('nuevo', 'nuevo@example.com', 'administrador'),
            ('admin', 'admin@example.com', 'estudiante'),
        ):
            response = self.client.post(reverse('registro_usuario'), {
                'username': username, 'email': email,
                'password1': 'Clave-Registro-2026!',
                'password2': 'Clave-Registro-2026!', 'tipo': tipo,
            })
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_rol_elegido_debe_coincidir_al_ingresar(self):
        self.client.post(reverse('registro_usuario'), {
            'username': 'familia', 'email': 'familia@example.com',
            'password1': 'Clave-Registro-2026!',
            'password2': 'Clave-Registro-2026!', 'tipo': 'familiar',
        })
        self.client.post(reverse('salir_estudiante'))
        incorrecto = self.client.post(reverse('acceso_estudiante'), {
            'username': 'familia', 'password': 'Clave-Registro-2026!',
            'tipo': 'estudiante',
        })
        self.assertContains(incorrecto, 'Usuario o contraseña incorrectos.')
        self.assertNotIn(STUDENT_ID_KEY, self.client.session)
        correcto = self.client.post(reverse('acceso_estudiante'), {
            'username': 'familia', 'password': 'Clave-Registro-2026!',
            'tipo': 'familiar',
        })
        self.assertRedirects(correcto, reverse('dashboard'))

    def test_solo_admin_accede_al_admin_y_gestiona_contenido(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'Clave-Admin-2026!')
        otro = User.objects.create_superuser('admin1', 'admin1@example.com', 'Clave-Admin-2026!')
        self.assertEqual(list(django_admin.site._registry), [Usuario])
        self.client.force_login(otro)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)
        self.assertEqual(self.client.get(reverse('panel_administracion')).status_code, 403)
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
        self.assertEqual(self.client.get(reverse('panel_administracion')).status_code, 200)
        self.assertEqual(self.client.get('/admin/auth/user/add/').status_code, 404)
        self.assertContains(self.client.get(reverse('admin:APP_usuario_changelist')), 'Usuario')

    def test_admin_ingresa_por_login_normal_y_aparece_en_dashboard(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'Clave-Admin-2026!')
        response = self.client.post(reverse('acceso_estudiante'), {
            'username': 'admin', 'password': 'Clave-Admin-2026!',
            'tipo': 'administrador',
        })
        self.assertRedirects(response, reverse('dashboard'))
        usuario = Usuario.objects.get(django_user=admin)
        self.assertEqual(usuario.username, 'admin')
        self.assertFalse(check_password('Clave-Admin-2026!', usuario.password))
        self.assertEqual(Perfil.objects.get(usuario=usuario).rol.codigo, 'administrador')
        self.assertContains(self.client.get(reverse('dashboard')), '¡Hola, admin!')
        self.assertContains(self.client.get(reverse('dashboard')), 'Panel de administración')
        self.assertEqual(self.client.get(reverse('panel_administracion')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:APP_usuario_change', args=[usuario.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse('admin:APP_usuario_delete', args=[usuario.pk]), {'post': 'yes'}).status_code, 403)
        self.client.post(reverse('salir_estudiante'))
        self.assertEqual(self.client.get(reverse('panel_administracion')).status_code, 302)

    def test_otro_superusuario_no_entra_por_acceso_administrador(self):
        User.objects.create_superuser('admin1', 'admin1@example.com', 'Clave-Admin-2026!')
        response = self.client.post(reverse('acceso_estudiante'), {
            'username': 'admin1', 'password': 'Clave-Admin-2026!',
            'tipo': 'administrador',
        })
        self.assertContains(response, 'Usuario o contraseña incorrectos.')
        self.assertFalse(Usuario.objects.filter(username='admin1').exists())

    def test_admin_que_ingreso_por_django_admin_ve_su_dashboard(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'Clave-Admin-2026!')
        self.client.force_login(admin)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '¡Hola, admin!')
        self.assertContains(response, 'Panel de administración')
        self.assertEqual(Usuario.objects.get(django_user=admin).username, 'admin')

    def test_ingresar_admin_despues_de_estudiante_cambia_identidad_de_aprendizaje(self):
        self.client.post(reverse('registro_usuario'), {
            'username': 'alumno', 'email': 'alumno@example.com',
            'password1': 'Clave-Alumno-2026!', 'password2': 'Clave-Alumno-2026!',
            'tipo': 'estudiante',
        })
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'Clave-Admin-2026!')
        self.assertTrue(self.client.login(username='admin', password='Clave-Admin-2026!'))
        dashboard = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard, '¡Hola, admin!')
        self.assertNotContains(dashboard, '¡Hola, alumno!')
        self.assertEqual(self.client.session[STUDENT_ID_KEY], Usuario.objects.get(django_user=admin).pk)
