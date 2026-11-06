from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
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

from . import forms
from .models import Leccion, Modulo, Perfil, Progreso, Rol, Usuario
from .student_session import start_student_session, student_from_request


def _learning_context(request):
    user = request.user
    permissions = ('APP.view_modulo', 'APP.view_leccion', 'APP.view_rol')
    return {
        'estudiante': student_from_request(request),
        'lectura_ampliada': request.COOKIES.get('lectura_ampliada') == '1',
        'can_manage_content': (
            user.is_authenticated and user.is_active and user.is_staff
            and any(user.has_perm(permission) for permission in permissions)
        ),
    }


def _student_profile(usuario):
    """Reutiliza el perfil del usuario aunque cambie el nombre de su rol."""
    with transaction.atomic():
        Usuario.objects.select_for_update().get(pk=usuario.pk)
        perfil = Perfil.objects.filter(usuario=usuario).order_by('pk').first()
        if perfil is not None:
            return perfil

        rol = Rol.objects.filter(nombre__iexact='Estudiante').order_by('pk').first()
        if rol is None:
            rol = Rol.objects.create(nombre='Estudiante', descripcion='Acceso al aprendizaje')
        return Perfil.objects.create(usuario=usuario, rol=rol)


@sensitive_post_parameters('password')
def acceso_estudiante(request):
    if student_from_request(request):
        return redirect('dashboard')

    form = forms.AccesoEstudianteForm(
        request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username'].strip()
        try:
            usuario = Usuario.objects.get(username__iexact=username)
        except (Usuario.DoesNotExist, Usuario.MultipleObjectsReturned):
            usuario = None

        if usuario is not None and check_password(form.cleaned_data['password'], usuario.password):
            _student_profile(usuario)
            start_student_session(request, usuario)
            return redirect('dashboard')
        form.add_error(None, 'Usuario o contraseña incorrectos.')

    return render(request, 'APP/learning/acceso.html', {'form': form})


@require_POST
def salir_estudiante(request):
    request.session.flush()
    return redirect('dashboard')


@require_POST
def preferencia_lectura(request):
    response = redirect('dashboard')
    destination = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        response['Location'] = destination

    if request.POST.get('lectura_ampliada') == '1':
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
            return redirect_to_login(request.get_full_path(), reverse('admin:login'))
        if not (
            user.is_active and user.is_staff and user.has_perm(self.permission_required)
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


class DashboardView(TemplateView):
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


class AprenderModuloView(TemplateView):
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


class ResponderLeccionView(View):
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
        if self.object.perfil_set.exists():
            # Conserva el rol mientras esté asignado a uno o más perfiles.
            messages.error(
                self.request,
                'No se puede eliminar este rol mientras esté asignado a perfiles.',
            )
            return redirect('rol_list')
        return super().form_valid(form)
