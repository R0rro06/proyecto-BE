from django.contrib import admin
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin_forms import UsuarioChangeAdminForm
from .models import Leccion, Modulo, Perfil, Progreso, Rol, Usuario


class UsuarioAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='Clave-Admin-2026!',
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_admin_de_django_y_usuario_del_proyecto_estan_disponibles(self):
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
        self.assertNotIn(User, admin.site._registry)
        self.assertEqual(list(admin.site._registry), [Usuario])
        self.assertEqual(
            self.client.get(reverse('admin:APP_usuario_changelist')).status_code, 200,
        )

    def test_grupos_no_se_administran_ni_se_asignan_desde_usuarios(self):
        Group.objects.create(name='Docentes')
        self.assertNotIn(Group, admin.site._registry)
        self.assertEqual(self.client.get('/admin/auth/group/').status_code, 404)
        self.assertEqual(self.client.get('/admin/auth/user/').status_code, 404)

    def test_usuario_anonimo_no_puede_administrar(self):
        self.client.logout()
        response = self.client.get(reverse('admin:APP_usuario_changelist'))
        self.assertRedirects(response, '/admin/login/?next=/admin/APP/usuario/')

    def test_usuario_autenticado_sin_permiso_no_puede_administrar(self):
        personal = User.objects.create_user(
            username='personal',
            password='Clave-Personal-2026!',
            is_staff=True,
        )
        self.client.force_login(personal)
        response = self.client.get(reverse('admin:APP_usuario_changelist'))
        self.assertEqual(response.status_code, 302)

    def test_crear_usuario_guarda_hash_y_no_expone_password(self):
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            'username': 'estudiante',
            'email': 'estudiante@example.com',
            'password1': 'Clave-Estudiante-2026!',
            'password2': 'Clave-Estudiante-2026!',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        usuario = Usuario.objects.get(username='estudiante')
        self.assertNotEqual(usuario.password, 'Clave-Estudiante-2026!')
        self.assertTrue(check_password('Clave-Estudiante-2026!', usuario.password))

        change = self.client.get(reverse('admin:APP_usuario_change', args=[usuario.pk]))
        self.assertEqual(change.status_code, 200)
        self.assertNotContains(change, usuario.password)
        self.assertNotContains(change, 'value="Clave-Estudiante-2026!"')

    def test_rechaza_contrasenas_distintas(self):
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            'username': 'estudiante',
            'email': 'estudiante@example.com',
            'password1': 'Clave-Estudiante-2026!',
            'password2': 'Otra-Clave-2026!',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Las contraseñas no coinciden.')
        self.assertFalse(Usuario.objects.filter(username='estudiante').exists())

    def test_rechaza_contrasena_similar_al_nombre_al_crear(self):
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            'username': 'CuentaNueva2026!',
            'email': 'cuenta@example.com',
            'password1': 'CuentaNueva2026!',
            'password2': 'CuentaNueva2026!',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='cuenta@example.com').exists())

    def test_contrasena_con_espacios_no_se_modifica(self):
        password = ' Clave-Estudiante-2026! '
        response = self.client.post(reverse('admin:APP_usuario_add'), {
            'username': 'estudiante',
            'email': 'estudiante@example.com',
            'password1': password,
            'password2': password,
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        usuario = Usuario.objects.get(username='estudiante')
        self.assertTrue(check_password(password, usuario.password))
        self.assertFalse(check_password(password.strip(), usuario.password))

    def test_editar_usuario_conserva_o_cambia_contrasena_segun_formulario(self):
        usuario = Usuario.objects.create(
            username='estudiante',
            email='estudiante@example.com',
            password=make_password('Clave-Original-2026!'),
        )
        url = reverse('admin:APP_usuario_change', args=[usuario.pk])
        original_hash = usuario.password

        response = self.client.post(url, {
            'username': 'estudiante',
            'email': 'nuevo@example.com',
            'new_password1': '',
            'new_password2': '',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        usuario.refresh_from_db()
        self.assertEqual(usuario.password, original_hash)
        self.assertEqual(usuario.email, 'nuevo@example.com')

        response = self.client.post(url, {
            'username': 'estudiante',
            'email': 'nuevo@example.com',
            'new_password1': 'Clave-Nueva-2026!',
            'new_password2': 'Clave-Nueva-2026!',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        usuario.refresh_from_db()
        self.assertTrue(check_password('Clave-Nueva-2026!', usuario.password))

    def test_rechaza_contrasena_similar_al_nuevo_nombre_al_editar(self):
        usuario = Usuario.objects.create(
            username='nombre-anterior',
            email='estudiante@example.com',
            password=make_password('Clave-Original-2026!'),
        )
        original_hash = usuario.password
        response = self.client.post(
            reverse('admin:APP_usuario_change', args=[usuario.pk]),
            {
                'username': 'CuentaNueva2026!',
                'email': 'estudiante@example.com',
                'new_password1': 'CuentaNueva2026!',
                'new_password2': 'CuentaNueva2026!',
                '_save': 'Guardar',
            },
        )
        self.assertEqual(response.status_code, 200)
        usuario.refresh_from_db()
        self.assertEqual(usuario.username, 'nombre-anterior')
        self.assertEqual(usuario.password, original_hash)

    def test_edicion_sin_clave_no_revierte_un_cambio_de_clave_concurrente(self):
        usuario = Usuario.objects.create(
            username='estudiante',
            email='estudiante@example.com',
            password=make_password('Clave-Original-2026!'),
        )
        formulario_antiguo = UsuarioChangeAdminForm({
            'username': 'estudiante',
            'email': 'nuevo@example.com',
            'new_password1': '',
            'new_password2': '',
        }, instance=Usuario.objects.get(pk=usuario.pk))
        self.assertTrue(formulario_antiguo.is_valid())

        usuario.password = make_password('Clave-Nueva-2026!')
        usuario.save(update_fields=('password',))

        usuario_admin = admin.site._registry[Usuario]
        request = RequestFactory().post('/admin/APP/usuario/')
        usuario_admin.save_model(
            request, formulario_antiguo.save(commit=False), formulario_antiguo,
            change=True,
        )

        usuario.refresh_from_db()
        self.assertEqual(usuario.email, 'nuevo@example.com')
        self.assertTrue(check_password('Clave-Nueva-2026!', usuario.password))

    def test_elimina_usuario_con_perfil_y_progreso_tras_confirmacion(self):
        usuario = Usuario.objects.create(
            username='estudiante',
            email='estudiante@example.com',
            password=make_password('Clave-Estudiante-2026!'),
        )
        rol = Rol.objects.create(nombre='Estudiante')
        perfil = Perfil.objects.create(usuario=usuario, rol=rol)
        otro_usuario = Usuario.objects.create(
            username='otro', email='otro@example.com',
            password=make_password('Clave-Otro-2026!'),
        )
        otro_perfil = Perfil.objects.create(usuario=otro_usuario, rol=rol)
        modulo = Modulo.objects.create(titulo='Inicio', descripcion='Contenido', orden=1)
        leccion = Leccion.objects.create(
            pregunta='¿Es correcto?', es_verdad=1, explicacion='Sí', modulo=modulo,
        )
        Progreso.objects.create(perfil=perfil, leccion=leccion, intentos=2)
        Progreso.objects.create(perfil=otro_perfil, leccion=leccion, intentos=1)

        url = reverse('admin:APP_usuario_delete', args=[usuario.pk])
        confirmacion = self.client.get(url)
        self.assertEqual(confirmacion.status_code, 200)
        self.assertTrue(Usuario.objects.filter(pk=usuario.pk).exists())
        self.assertContains(confirmacion, 'Progreso')

        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Usuario.objects.filter(pk=usuario.pk).exists())
        self.assertFalse(Perfil.objects.filter(pk=perfil.pk).exists())
        self.assertFalse(Progreso.objects.filter(perfil_id=perfil.pk).exists())
        self.assertTrue(Usuario.objects.filter(pk=otro_usuario.pk).exists())
        self.assertEqual(Progreso.objects.filter(perfil=otro_perfil).count(), 1)
        self.assertTrue(Rol.objects.filter(pk=rol.pk).exists())
        self.assertTrue(Leccion.objects.filter(pk=leccion.pk).exists())

    def test_elimina_usuario_sin_perfil(self):
        usuario = Usuario.objects.create(
            username='estudiante',
            email='estudiante@example.com',
            password=make_password('Clave-Estudiante-2026!'),
        )
        response = self.client.post(
            reverse('admin:APP_usuario_delete', args=[usuario.pk]),
            {'post': 'yes'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Usuario.objects.filter(pk=usuario.pk).exists())
