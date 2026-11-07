"""Regresiones para el uso de Django Auth en las cuentas de aprendizaje."""

from django.contrib import admin
from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import RequestFactory
from django.test import Client, TestCase
from django.urls import reverse

from .models import Perfil, Usuario


User = get_user_model()


class DjangoAuthFlowTests(TestCase):
    password = 'Clave-Registro-2026!'

    def register(self, username, role):
        return self.client.post(reverse('registro_usuario'), {
            'username': username,
            'email': f'{username}@example.com',
            'password1': self.password,
            'password2': self.password,
            'tipo': role,
        })

    def test_registro_crea_cuenta_auth_y_conserva_perfil_y_rol(self):
        response = self.register('familia', 'familiar')
        self.assertRedirects(response, reverse('dashboard'))
        usuario = Usuario.objects.get(username='familia')
        account = User.objects.get(username='familia')
        self.assertEqual(usuario.django_user_id, account.pk)
        self.assertTrue(account.check_password(self.password))
        self.assertEqual(Perfil.objects.get(usuario=usuario).rol.codigo, 'familiar')
        self.assertEqual(int(self.client.session[SESSION_KEY]), account.pk)
        self.assertNotIn('app_usuario_id', self.client.session)

    def test_login_no_depende_del_tipo_seleccionado(self):
        self.register('profesor', 'profesor')
        self.client.post(reverse('salir_estudiante'))

        response = self.client.post(reverse('acceso_estudiante'), {
            'username': 'profesor', 'password': self.password, 'tipo': 'estudiante',
        })

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session[SESSION_KEY]),
                         User.objects.get(username='profesor').pk)

    def test_las_cuatro_categorias_pueden_iniciar_sesion(self):
        for role in ('estudiante', 'familiar', 'profesor', 'otro'):
            with self.subTest(role=role):
                client = Client()
                client.post(reverse('registro_usuario'), {
                    'username': role, 'email': f'{role}@example.com',
                    'password1': self.password, 'password2': self.password,
                    'tipo': role,
                })
                client.post(reverse('salir_estudiante'))
                response = client.post(reverse('acceso_estudiante'), {
                    'username': role, 'password': self.password,
                })
                self.assertRedirects(response, reverse('dashboard'))
                self.assertEqual(int(client.session[SESSION_KEY]),
                                 User.objects.get(username=role).pk)

    def test_logout_invalida_acceso_y_sesion_legacy_no_autentica(self):
        self.register('alumno', 'estudiante')
        self.client.post(reverse('salir_estudiante'))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)

        session = self.client.session
        session['app_usuario_id'] = Usuario.objects.get(username='alumno').pk
        session.save()
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_cambio_de_clave_en_admin_invalida_sesion_existente(self):
        self.register('alumno', 'estudiante')
        usuario = Usuario.objects.get(username='alumno')
        student_client = self.client
        admin_client = Client()
        admin_user = User.objects.create_superuser(
            'admin', 'admin@example.com', 'Clave-Admin-2026!',
        )
        admin_client.force_login(admin_user)

        response = admin_client.post(reverse('admin:APP_usuario_change', args=[usuario.pk]), {
            'username': 'alumno', 'email': 'alumno@example.com',
            'tipo': 'estudiante',
            'new_password1': 'Clave-Cambiada-2026!',
            'new_password2': 'Clave-Cambiada-2026!', '_save': 'Guardar',
        })

        self.assertEqual(response.status_code, 302, response.content.decode(errors='replace'))
        self.assertEqual(student_client.get(reverse('dashboard')).status_code, 302)
        self.assertNotIn(SESSION_KEY, student_client.session)

    def test_solo_admin_principal_puede_entrar_al_panel_de_contenido(self):
        primary = User.objects.create_superuser('admin', 'admin@example.com', 'Clave-Admin-2026!')
        second = User.objects.create_superuser('admin1', 'admin1@example.com', 'Clave-Admin-2026!')
        panel = reverse('panel_administracion')

        self.client.force_login(second)
        self.assertEqual(self.client.get(panel).status_code, 403)
        self.client.force_login(primary)
        self.assertEqual(self.client.get(panel).status_code, 200)

    def test_admin_django_sigue_siendo_solo_para_la_cuenta_principal(self):
        User.objects.create_superuser('admin1', 'admin1@example.com', 'Clave-Admin-2026!')
        self.assertNotIn(User, admin.site._registry)
        self.assertNotIn('auth/group', [model._meta.label_lower for model in admin.site._registry])
        self.client.force_login(User.objects.get(username='admin1'))
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)


class UsuarioAdminAuthSyncTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            'admin', 'admin@example.com', 'Clave-Admin-2026!',
        )
        self.client.force_login(self.admin_user)

    def test_creacion_admin_sincroniza_usuario_y_hash_de_django(self):
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            'username': 'gestionado', 'email': 'gestionado@example.com',
            'tipo': 'estudiante',
            'password1': 'Clave-Gestion-2026!',
            'password2': 'Clave-Gestion-2026!', '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        usuario = Usuario.objects.get(username='gestionado')
        account = get_user_model().objects.get(username='gestionado')
        self.assertEqual(usuario.django_user_id, account.pk)
        self.assertTrue(account.check_password('Clave-Gestion-2026!'))

    def test_editar_y_eliminar_admin_sincroniza_ambas_cuentas(self):
        account = get_user_model().objects.create_user(
            username='gestionado', email='old@example.com', password='Clave-Original-2026!',
        )
        usuario = Usuario.objects.create(
            username='gestionado', email='old@example.com', password='!', django_user=account,
        )
        edit = reverse('admin:APP_usuario_change', args=[usuario.pk])
        response = self.client.post(edit, {
            'username': 'gestionado', 'email': 'new@example.com',
            'tipo': 'estudiante',
            'new_password1': 'Clave-Nueva-2026!',
            'new_password2': 'Clave-Nueva-2026!', '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.admin_user.pk)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
        account.refresh_from_db()
        self.assertEqual(account.email, 'new@example.com')
        self.assertTrue(account.check_password('Clave-Nueva-2026!'))
        request = RequestFactory().get('/admin/APP/usuario/')
        request.user = self.admin_user
        self.assertTrue(admin.site._registry[Usuario].has_delete_permission(request, usuario))

        response = self.client.post(
            reverse('admin:APP_usuario_delete', args=[usuario.pk]), {'post': 'yes'},
        )
        self.assertEqual(response.status_code, 302, response.content.decode(errors='replace'))
        self.assertFalse(Usuario.objects.filter(pk=usuario.pk).exists())
        self.assertFalse(get_user_model().objects.filter(pk=account.pk).exists())
