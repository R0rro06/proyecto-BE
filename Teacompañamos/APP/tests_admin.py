from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .models import Estado, Leccion, Modulo, Perfil, Progreso, Rol, Usuario


def crear_usuario(username, email, password='Clave-Estudiante-2026!'):
    account = User.objects.create_user(username=username, email=email, password=password)
    return Usuario.objects.create(
        username=username, email=email, password=make_password(None), django_user=account,
    )


class UsuarioAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='Clave-Admin-2026!',
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_admin_personalizado_registra_datos_y_oculta_grupos_y_auth_user(self):
        for model in (Usuario, Rol, Perfil):
            self.assertIn(model, admin.site._registry)
        for model in (Modulo, Leccion, Progreso, Estado):
            self.assertNotIn(model, admin.site._registry)
        self.assertNotIn(User, admin.site._registry)
        self.assertNotIn(Group, admin.site._registry)
        self.assertEqual(self.client.get('/admin/auth/user/').status_code, 404)
        self.assertEqual(self.client.get('/admin/auth/group/').status_code, 404)
        self.assertEqual(self.client.get(reverse('admin:APP_usuario_changelist')).status_code, 200)
        index = self.client.get(reverse('admin:index'))
        self.assertContains(index, 'Usuarios')
        self.assertContains(index, 'Roles')
        self.assertContains(index, 'Perfiles')
        self.assertNotContains(index, 'Módulos')
        self.assertNotContains(index, 'Lecciones')
        for path in ('modulo', 'leccion', 'progreso', 'estado'):
            self.assertEqual(self.client.get(f'/admin/APP/{path}/').status_code, 404)

    def test_perfil_permite_cambiar_rol_sin_exponer_rol_administrador(self):
        usuario = crear_usuario('estudiante', 'estudiante@example.com')
        perfil = Perfil.objects.create(usuario=usuario, rol=Rol.objects.get(codigo='estudiante'))
        url = reverse('admin:APP_perfil_change', args=[perfil.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        admin_role = Rol.objects.get(codigo='administrador')
        self.assertNotContains(page, f'<option value="{admin_role.pk}"')
        response = self.client.post(url, {'rol': Rol.objects.get(codigo='familiar').pk, '_save': 'Guardar'})
        self.assertEqual(response.status_code, 302)
        perfil.refresh_from_db()
        self.assertEqual(perfil.rol.codigo, 'familiar')

    def test_anonimo_y_staff_sin_permisos_no_administran(self):
        self.client.logout()
        response = self.client.get(reverse('admin:APP_usuario_changelist'))
        self.assertEqual(response.status_code, 302)
        staff = User.objects.create_user('personal', password='Clave-Personal-2026!', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('admin:APP_usuario_changelist')).status_code, 302)

    def test_crear_usuario_guarda_hash_en_django_y_asigna_rol(self):
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            'username': 'estudiante', 'email': 'estudiante@example.com', 'tipo': 'estudiante',
            'password1': 'Clave-Estudiante-2026!', 'password2': 'Clave-Estudiante-2026!',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        usuario = Usuario.objects.get(username='estudiante')
        account = User.objects.get(username='estudiante')
        self.assertEqual(usuario.django_user_id, account.pk)
        self.assertFalse(account.is_staff)
        self.assertFalse(account.is_superuser)
        self.assertTrue(account.check_password('Clave-Estudiante-2026!'))
        self.assertEqual(Perfil.objects.get(usuario=usuario).rol.codigo, 'estudiante')
        change = self.client.get(reverse('admin:APP_usuario_change', args=[usuario.pk]))
        self.assertNotContains(change, account.password)
        self.assertNotContains(change, 'value="Clave-Estudiante-2026!"')

    def test_rechaza_claves_distintas_similares_y_usuario_duplicado(self):
        base = {'username': 'estudiante', 'email': 'estudiante@example.com', 'tipo': 'estudiante'}
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            **base, 'password1': 'Clave-Estudiante-2026!', 'password2': 'Otra-Clave-2026!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='estudiante').exists())
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            **base, 'password1': 'estudiante', 'password2': 'estudiante',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Usuario.objects.exists())
        crear_usuario('estudiante', 'estudiante@example.com')
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            **base, 'password1': 'Clave-Estudiante-2026!', 'password2': 'Clave-Estudiante-2026!',
        })
        self.assertEqual(response.status_code, 200)

    def test_clave_con_espacios_se_preserva_exactamente(self):
        password = ' Clave-Estudiante-2026! '
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            'username': 'estudiante', 'email': 'estudiante@example.com', 'tipo': 'estudiante',
            'password1': password, 'password2': password, '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        account = User.objects.get(username='estudiante')
        self.assertTrue(account.check_password(password))
        self.assertFalse(account.check_password(password.strip()))

    def test_editar_cambia_datos_y_clave_o_preserva_clave(self):
        usuario = crear_usuario('estudiante', 'estudiante@example.com', 'Clave-Original-2026!')
        account = usuario.django_user
        url = reverse('admin:APP_usuario_change', args=[usuario.pk])
        response = self.client.post(url, {
            'username': 'estudiante', 'email': 'nuevo@example.com', 'tipo': 'familiar',
            'new_password1': '', 'new_password2': '', '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        account.refresh_from_db()
        self.assertEqual(account.email, 'nuevo@example.com')
        self.assertTrue(account.check_password('Clave-Original-2026!'))
        self.assertEqual(Perfil.objects.get(usuario=usuario).rol.codigo, 'familiar')
        response = self.client.post(url, {
            'username': 'estudiante', 'email': 'nuevo@example.com', 'tipo': 'familiar',
            'new_password1': 'Clave-Nueva-2026!', 'new_password2': 'Clave-Nueva-2026!',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        account.refresh_from_db()
        self.assertTrue(account.check_password('Clave-Nueva-2026!'))

    def test_eliminar_usuario_cascada_su_progreso_sin_afectar_otros(self):
        usuario = crear_usuario('estudiante', 'estudiante@example.com')
        account_id = usuario.django_user_id
        rol = Rol.objects.get(codigo='estudiante')
        perfil = Perfil.objects.create(usuario=usuario, rol=rol)
        otro = crear_usuario('otro', 'otro@example.com')
        otro_perfil = Perfil.objects.create(usuario=otro, rol=rol)
        modulo = Modulo.objects.create(titulo='Inicio', descripcion='Contenido', orden=1)
        leccion = Leccion.objects.create(
            pregunta='¿Correcto?', es_verdad=1, explicacion='Sí', modulo=modulo,
        )
        Progreso.objects.create(perfil=perfil, leccion=leccion, intentos=2)
        Progreso.objects.create(perfil=otro_perfil, leccion=leccion, intentos=1)
        url = reverse('admin:APP_usuario_delete', args=[usuario.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Usuario.objects.filter(pk=usuario.pk).exists())
        self.assertFalse(User.objects.filter(pk=account_id).exists())
        self.assertFalse(Perfil.objects.filter(pk=perfil.pk).exists())
        self.assertFalse(Progreso.objects.filter(perfil=perfil).exists())
        self.assertTrue(Usuario.objects.filter(pk=otro.pk).exists())
        self.assertEqual(Progreso.objects.filter(perfil=otro_perfil).count(), 1)
        self.assertTrue(Leccion.objects.filter(pk=leccion.pk).exists())

    def test_admin_principal_no_se_puede_eliminar(self):
        admin_learning = Usuario.objects.create(
            username='admin', email='admin@example.com', password=make_password(None),
            django_user=self.admin_user,
        )
        response = self.client.post(
            reverse('admin:APP_usuario_delete', args=[admin_learning.pk]), {'post': 'yes'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Usuario.objects.filter(pk=admin_learning.pk).exists())
