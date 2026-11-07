from django.contrib import admin as django_admin
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Leccion, Modulo, Perfil, Rol, Usuario


class AccesoYRegistroTests(TestCase):
    def test_inicio_antes_del_dashboard_y_proteccion_de_lecciones(self):
        modulo = Modulo.objects.create(titulo='Inicio', descripcion='Contenido', orden=1)
        leccion = Leccion.objects.create(
            pregunta='¿Es verdadero?', es_verdad=1, explicacion='Sí', modulo=modulo,
        )
        inicio = self.client.get(reverse('inicio'))
        self.assertEqual(inicio.status_code, 200)
        self.assertContains(inicio, reverse('acceso_estudiante'))
        self.assertContains(inicio, reverse('registro_usuario'))
        for url in (reverse('dashboard'), reverse('aprender_modulo', args=[modulo.pk]),
                    reverse('responder_leccion', args=[leccion.pk])):
            self.assertEqual(self.client.get(url).status_code, 302)
            self.assertEqual(self.client.post(url, {'respuesta': '1'}).status_code, 302)

    def test_registro_crea_usuario_perfil_y_sesion_para_cada_tipo(self):
        for codigo in ('estudiante', 'familiar', 'profesor', 'otro'):
            client = Client()
            response = client.post(reverse('registro_usuario'), {
                'username': codigo, 'email': f'{codigo}@example.com',
                'password1': 'Clave-Registro-2026!',
                'password2': 'Clave-Registro-2026!', 'tipo': codigo,
            })
            self.assertRedirects(response, reverse('dashboard'))
            usuario = Usuario.objects.get(username=codigo)
            self.assertFalse(check_password('Clave-Registro-2026!', usuario.password))
            self.assertEqual(Perfil.objects.get(usuario=usuario).rol.codigo, codigo)
            account = User.objects.get(username=codigo)
            self.assertTrue(account.check_password('Clave-Registro-2026!'))
            self.assertEqual(usuario.django_user_id, account.pk)
            self.assertEqual(int(client.session[SESSION_KEY]), account.pk)
            self.assertRedirects(client.get(reverse('inicio')), reverse('dashboard'))

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

    def test_login_no_depende_del_rol_seleccionado(self):
        self.client.post(reverse('registro_usuario'), {
            'username': 'familia', 'email': 'familia@example.com',
            'password1': 'Clave-Registro-2026!',
            'password2': 'Clave-Registro-2026!', 'tipo': 'familiar',
        })
        client = Client()
        incorrecto = client.post(reverse('acceso_estudiante'), {
            'username': 'familia', 'password': 'Clave-Registro-2026!',
            'tipo': 'estudiante',
        })
        self.assertRedirects(incorrecto, reverse('dashboard'))
        self.assertEqual(int(client.session[SESSION_KEY]), User.objects.get(username='familia').pk)
        client.post(reverse('salir_estudiante'))
        correcto = client.post(reverse('acceso_estudiante'), {
            'username': 'familia', 'password': 'Clave-Registro-2026!',
            'tipo': 'familiar',
        })
        self.assertRedirects(correcto, reverse('dashboard'))

    def test_solo_admin_accede_al_admin_y_gestiona_contenido(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'Clave-Admin-2026!')
        otro = User.objects.create_superuser('admin1', 'admin1@example.com', 'Clave-Admin-2026!')
        self.assertIn(Usuario, django_admin.site._registry)
        self.assertIn(Rol, django_admin.site._registry)
        self.assertIn(Perfil, django_admin.site._registry)
        self.assertNotIn(Modulo, django_admin.site._registry)
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

    def test_enlace_administrador_inicia_sesion_y_abre_panel(self):
        self.assertContains(self.client.get(reverse('inicio')), 'Iniciar sesión como administrador')
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'Clave-Admin-2026!')
        url = f"{reverse('acceso_estudiante')}?tipo=administrador&next={reverse('panel_administracion')}"
        self.assertContains(self.client.get(url), 'Acceso de administración')
        response = self.client.post(url, {
            'username': 'admin', 'password': 'Clave-Admin-2026!',
            'tipo': 'administrador', 'next': reverse('panel_administracion'),
        })
        self.assertRedirects(response, reverse('panel_administracion'))
        self.assertEqual(int(self.client.session[SESSION_KEY]), admin.pk)

    def test_acceso_administrador_rechaza_cuenta_normal(self):
        self.client.post(reverse('registro_usuario'), {
            'username': 'alumno', 'email': 'alumno@example.com',
            'password1': 'Clave-Alumno-2026!', 'password2': 'Clave-Alumno-2026!',
            'tipo': 'estudiante',
        })
        self.client.post(reverse('salir_estudiante'))
        response = self.client.post(reverse('acceso_estudiante'), {
            'username': 'alumno', 'password': 'Clave-Alumno-2026!',
            'tipo': 'administrador', 'next': reverse('panel_administracion'),
        })
        self.assertContains(response, 'Usuario o contraseña incorrectos.')
        self.assertNotIn(SESSION_KEY, self.client.session)

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
        self.assertEqual(int(self.client.session[SESSION_KEY]), admin.pk)
