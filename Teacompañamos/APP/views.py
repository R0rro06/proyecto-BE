from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from urllib.parse import urlencode

from . import forms
from .admin_account import ensure_admin_learning_user, is_primary_admin
from .models import Leccion, Modulo, Perfil, Progreso, Rol, Usuario
from .student_session import start_student_session, student_from_request


def _safe_destination(request, fallback='dashboard'):
    destination = request.POST.get('next') or request.GET.get('next', '')
    if destination.startswith('/') and not destination.startswith('//') and url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return destination
    return reverse(fallback)


def _selected_type(request):
    value = request.POST.get('tipo') or request.GET.get('tipo')
    return value if value in dict((*forms.TIPOS_USUARIO, ('administrador', 'Administrador'))) else 'estudiante'


def _learning_user(request):
    if is_primary_admin(request.user):
        usuario = student_from_request(request)
        if usuario and usuario.django_user_id == request.user.pk:
            return usuario
        usuario = ensure_admin_learning_user(request.user)
        start_student_session(request, usuario)
        return usuario
    return student_from_request(request)


def inicio(request):
    if _learning_user(request):
        return redirect('dashboard')
    return render(request, 'APP/learning/inicio.html', {
        'tipos': forms.TIPOS_USUARIO,
        'next': _safe_destination(request),
        'lectura_ampliada': request.COOKIES.get('lectura_ampliada') == '1',
    })


class StudentRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if _learning_user(request) is None:
            return redirect(f"{reverse('inicio')}?{urlencode({'next': request.get_full_path()})}")
        return super().dispatch(request, *args, **kwargs)


def _learning_context(request):
    return {
        'estudiante': _learning_user(request),
        'lectura_ampliada': request.COOKIES.get('lectura_ampliada') == '1',
        'can_manage_content': is_primary_admin(request.user),
    }


def _student_profile(usuario):
    """Reutiliza el perfil del usuario aunque cambie el nombre de su rol."""
    with transaction.atomic():
        Usuario.objects.select_for_update().get(pk=usuario.pk)
        perfil = Perfil.objects.filter(usuario=usuario).order_by('pk').first()
        if perfil is not None:
            return perfil

        rol = Rol.objects.filter(codigo='estudiante').first()
        if rol is None:
            rol = Rol.objects.filter(nombre__iexact='Estudiante').order_by('pk').first()
        if rol is None:
            rol = Rol.objects.create(codigo='estudiante', nombre='Estudiante', descripcion='Acceso al aprendizaje')
        return Perfil.objects.create(usuario=usuario, rol=rol)


@sensitive_post_parameters('password')
def acceso_estudiante(request):
    if _learning_user(request):
        return redirect('dashboard')

    form = forms.AccesoEstudianteForm(
        request.POST if request.method == 'POST' else None,
    )
    tipo = _selected_type(request)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username'].strip()
        if tipo == 'administrador':
            admin_user = authenticate(request, username=username, password=form.cleaned_data['password'])
            if admin_user is not None and is_primary_admin(admin_user):
                login(request, admin_user)
                usuario_admin = ensure_admin_learning_user(admin_user)
                start_student_session(request, usuario_admin)
                return redirect(_safe_destination(request))
            form.add_error(None, 'Usuario o contraseña incorrectos.')
            return render(request, 'APP/learning/acceso.html', {
                'form': form, 'tipo': tipo, 'tipo_nombre': 'Administrador',
                'next': _safe_destination(request),
            })
        try:
            usuario = Usuario.objects.get(username__iexact=username, django_user__isnull=True)
        except (Usuario.DoesNotExist, Usuario.MultipleObjectsReturned):
            usuario = None

        if usuario is not None and check_password(form.cleaned_data['password'], usuario.password):
            perfil = _student_profile(usuario)
            if perfil.rol.codigo == tipo:
                start_student_session(request, usuario)
                return redirect(_safe_destination(request))
        form.add_error(None, 'Usuario o contraseña incorrectos.')

    return render(request, 'APP/learning/acceso.html', {
        'form': form, 'tipo': tipo,
        'tipo_nombre': dict((*forms.TIPOS_USUARIO, ('administrador', 'Administrador')))[tipo],
        'next': _safe_destination(request),
    })


@sensitive_post_parameters('password1', 'password2')
def registro_usuario(request):
    if _learning_user(request):
        return redirect('dashboard')
    tipo = _selected_type(request)
    if tipo == 'administrador':
        tipo = 'estudiante'
    form = forms.RegistroUsuarioForm(request.POST if request.method == 'POST' else None,
                                     initial={'tipo': tipo})
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                rol = Rol.objects.get(codigo=form.cleaned_data['tipo'])
                usuario = form.save()
                Perfil.objects.create(usuario=usuario, rol=rol)
        except IntegrityError:
            form.add_error(None, 'El usuario o correo ya está registrado. Revisa los datos.')
        else:
            start_student_session(request, usuario)
            return redirect(_safe_destination(request))
    return render(request, 'APP/learning/registro.html', {
        'form': form, 'tipo': tipo, 'next': _safe_destination(request),
    })


@require_POST
def salir_estudiante(request):
    request.session.flush()
    return redirect('inicio')


@require_POST
def consentimiento_cookies(request):
    choice = request.POST.get('consentimiento')
    if choice not in ('aceptar', 'rechazar'):
        return HttpResponse('Elección de cookies no válida.', status=400)
    response = redirect(_safe_destination(request, fallback='inicio'))
    response.set_cookie(
        'consentimiento_cookies', choice, max_age=180 * 24 * 60 * 60,
        httponly=True, samesite='Lax', secure=request.is_secure(),
    )
    if choice == 'rechazar':
        response.delete_cookie('lectura_ampliada', samesite='Lax')
        response.delete_cookie('tema', samesite='Lax')
    return response


@require_POST
def preferencia_tema(request):
    tema = request.POST.get('tema')
    if tema not in ('claro', 'oscuro'):
        return HttpResponse('Tema no válido.', status=400)
    response = redirect(_safe_destination(request, fallback='inicio'))
    if request.COOKIES.get('consentimiento_cookies') == 'aceptar':
        response.set_cookie(
            'tema', tema, max_age=180 * 24 * 60 * 60,
            httponly=True, samesite='Lax', secure=request.is_secure(),
        )
    return response


@require_POST
def preferencia_lectura(request):
    response = redirect('dashboard')
    destination = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        response['Location'] = destination

    if (request.POST.get('lectura_ampliada') == '1'
            and request.COOKIES.get('consentimiento_cookies') == 'aceptar'):
        response.set_cookie(
            'lectura_ampliada', '1', max_age=30 * 24 * 60 * 60,
            httponly=True, samesite='Lax', secure=request.is_secure(),
        )
    else:
        response.delete_cookie('lectura_ampliada', samesite='Lax')
    return response


class ContentAdminMixin:
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect(f"{reverse('acceso_estudiante')}?{urlencode({'tipo': 'administrador', 'next': request.get_full_path()})}")
        if not (
            is_primary_admin(user) and user.has_perm(self.permission_required)
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PanelAdminView(ContentAdminMixin, TemplateView):
    template_name = 'APP/admin/panel_admin.html'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        self.permission_required = next((
            permission for permission in ('APP.view_modulo', 'APP.view_leccion', 'APP.view_rol')
            if user.has_perm(permission)
        ), 'APP.view_modulo')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(StudentRequiredMixin, TemplateView):
    """Muestra el catálogo y el avance individual cuando hay una sesión válida."""

    template_name = 'APP/learning/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_learning_context(self.request))
        modulos = list(
            Modulo.objects.order_by('orden').prefetch_related(
                Prefetch(
                    'leccion_set',
                    queryset=Leccion.objects.order_by('id'),
                    to_attr='lecciones',
                )
            )
        )
        context['modulos'] = modulos
        context['total_modulos'] = len(modulos)
        context['total_lecciones'] = sum(len(modulo.lecciones) for modulo in modulos)
        if context['estudiante']:
            perfil = _student_profile(context['estudiante'])
            context['lecciones_completadas'] = (
                Progreso.objects.filter(perfil=perfil, fecha_completada__isnull=False)
                .values('leccion_id').distinct().count()
            )
        return context


class AprenderModuloView(StudentRequiredMixin, TemplateView):
    """Carga un módulo y sus lecciones para la página de aprendizaje."""

    template_name = 'APP/learning/modulo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_learning_context(self.request))
        context['modulo'] = get_object_or_404(
            Modulo.objects.prefetch_related(
                Prefetch(
                    'leccion_set',
                    queryset=Leccion.objects.order_by('id'),
                    to_attr='lecciones',
                )
            ),
            pk=kwargs['pk'],
        )
        return context


class ResponderLeccionView(StudentRequiredMixin, View):
    template_name = 'APP/learning/leccion.html'

    def get_leccion(self, pk):
        return get_object_or_404(
            Leccion.objects.select_related('modulo'),
            pk=pk,
        )

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        leccion = self.get_leccion(pk)
        context = _learning_context(request)
        context.update({'leccion': leccion, 'form': forms.RespuestaLeccionForm()})
        return render(
            request, self.template_name, context,
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        leccion = self.get_leccion(pk)
        form = forms.RespuestaLeccionForm(request.POST)
        context = _learning_context(request)
        context.update({'leccion': leccion, 'form': form})

        if form.is_valid():
            context['respuesta_enviada'] = True
            context['es_correcta'] = (
                form.cleaned_data['respuesta'] == bool(leccion.es_verdad)
            )
            if context['estudiante']:
                perfil = _student_profile(context['estudiante'])
                with transaction.atomic():
                    Perfil.objects.select_for_update().get(pk=perfil.pk)
                    progreso = Progreso.objects.filter(
                        perfil=perfil, leccion=leccion,
                    ).order_by('pk').first()
                    if progreso is None:
                        progreso = Progreso(perfil=perfil, leccion=leccion, intentos=0)
                    progreso.intentos += 1
                    if context['es_correcta'] and progreso.fecha_completada is None:
                        progreso.fecha_completada = timezone.now()
                    progreso.save()
        else:
            return render(request, self.template_name, context, status=400)

        return render(request, self.template_name, context)


class CursosModuloListView(ContentAdminMixin, ListView):
    permission_required = 'APP.view_modulo'
    model = Modulo
    template_name = 'APP/admin/modulos/list.html'
    context_object_name = 'modulos'

    def get_queryset(self):
        queryset = super().get_queryset()
        termino = self.request.GET.get('q', '').strip()
        orden = self.request.GET.get('orden', '').strip()

        # Combina la búsqueda por texto con el filtro de orden, si se enviaron.
        if termino:
            queryset = queryset.filter(
                Q(titulo__icontains=termino) | Q(descripcion__icontains=termino)
            )
        if orden.isdecimal():
            queryset = queryset.filter(orden=int(orden))

        return queryset.order_by('orden')


class CursosModuloCreateView(ContentAdminMixin, CreateView):
    permission_required = 'APP.add_modulo'
    model = Modulo
    form_class = forms.ModuloForm
    template_name = 'APP/admin/modulos/form.html'
    success_url = reverse_lazy('cursos_modulo_list')

class CursosModuloUpdateView(ContentAdminMixin, UpdateView):
    permission_required = 'APP.change_modulo'
    model = Modulo
    form_class = forms.ModuloForm
    template_name = 'APP/admin/modulos/form.html'
    success_url = reverse_lazy('cursos_modulo_list')

class CursosModuloDeleteView(ContentAdminMixin, DeleteView):
    permission_required = 'APP.delete_modulo'
    model = Modulo
    template_name = 'APP/admin/modulos/confirm_delete.html'
    success_url = reverse_lazy('cursos_modulo_list')

    def form_valid(self, form):
        if self.object.leccion_set.exists():
            # No se puede borrar un módulo mientras sus lecciones dependan de él.
            messages.error(
                self.request,
                f'No se puede eliminar el módulo «{self.object.titulo}» porque contiene lecciones. '
                'Primero elimina esas lecciones o muévelas a otro módulo.',
            )
            return redirect('cursos_modulo_list')
        return super().form_valid(form)






class CursosLeccionListView(ContentAdminMixin, ListView):
    permission_required = 'APP.view_leccion'
    model = Leccion
    template_name = 'APP/admin/lecciones/list.html'
    context_object_name = 'lecciones'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('modulo')
        termino = self.request.GET.get('q', '').strip()
        modulo_id = self.request.GET.get('modulo', '').strip()
        respuesta = self.request.GET.get('respuesta', '').strip()

        # Los filtros de texto, módulo y respuesta se pueden combinar.
        if termino:
            queryset = queryset.filter(
                Q(pregunta__icontains=termino) | Q(explicacion__icontains=termino)
            )
        if modulo_id.isdecimal():
            queryset = queryset.filter(modulo_id=int(modulo_id))
        if respuesta in {'0', '1'}:
            queryset = queryset.filter(es_verdad=int(respuesta))

        return queryset.order_by('modulo__orden', 'id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modulos_filtro'] = Modulo.objects.order_by('orden')
        return context


class CursosLeccionCreateView(ContentAdminMixin, CreateView):
    permission_required = 'APP.add_leccion'
    model = Leccion
    form_class = forms.LeccionForm
    template_name = 'APP/admin/lecciones/form.html'
    success_url = reverse_lazy('cursos_leccion_list')

class CursosLeccionUpdateView(ContentAdminMixin, UpdateView):
    permission_required = 'APP.change_leccion'
    model = Leccion
    form_class = forms.LeccionForm
    template_name = 'APP/admin/lecciones/form.html'
    success_url = reverse_lazy('cursos_leccion_list')

class CursosLeccionDeleteView(ContentAdminMixin, DeleteView):
    permission_required = 'APP.delete_leccion'
    model = Leccion
    template_name = 'APP/admin/lecciones/confirm_delete.html'
    success_url = reverse_lazy('cursos_leccion_list')

    def form_valid(self, form):
        if self.object.progreso_set.exists():
            # Impide eliminar una lección que ya tiene progreso asociado.
            messages.error(
                self.request,
                'No se puede eliminar la lección mientras tenga progreso asociado.',
            )
            return redirect('cursos_leccion_list')
        return super().form_valid(form)


class RolListView(ContentAdminMixin, ListView):
    permission_required = 'APP.view_rol'
    model = Rol
    template_name = 'APP/admin/roles/list.html'
    context_object_name = 'roles'

    def get_queryset(self):
        queryset = super().get_queryset()
        termino = self.request.GET.get('q', '').strip()
        if termino:
            queryset = queryset.filter(
                Q(nombre__icontains=termino) | Q(descripcion__icontains=termino)
            )
        return queryset.annotate(perfiles_count=Count('perfil')).order_by('nombre')


class RolCreateView(ContentAdminMixin, CreateView):
    permission_required = 'APP.add_rol'
    model = Rol
    form_class = forms.RolForm
    template_name = 'APP/admin/roles/form.html'
    success_url = reverse_lazy('rol_list')


class RolUpdateView(ContentAdminMixin, UpdateView):
    permission_required = 'APP.change_rol'
    model = Rol
    form_class = forms.RolForm
    template_name = 'APP/admin/roles/form.html'
    success_url = reverse_lazy('rol_list')


class RolDeleteView(ContentAdminMixin, DeleteView):
    permission_required = 'APP.delete_rol'
    model = Rol
    template_name = 'APP/admin/roles/confirm_delete.html'
    success_url = reverse_lazy('rol_list')

    def form_valid(self, form):
        if self.object.codigo or self.object.perfil_set.exists():
            # Conserva el rol mientras esté asignado a uno o más perfiles.
            messages.error(
                self.request,
                'No se puede eliminar este rol mientras esté asignado a perfiles.',
            )
            return redirect('rol_list')
        return super().form_valid(form)
