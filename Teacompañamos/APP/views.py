from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Count, Prefetch, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views import View

from . import forms
from .models import Leccion, Modulo, Rol, Usuario
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy


class PanelAdminView(TemplateView):
    template_name = 'APP/admin/panel_admin.html'


class DashboardView(TemplateView):
    """Muestra los módulos y lecciones disponibles, sin progreso personal."""

    template_name = 'APP/learning/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        return context


class AprenderModuloView(TemplateView):
    """Carga un módulo y sus lecciones para la página de aprendizaje."""

    template_name = 'APP/learning/modulo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        return render(
            request,
            self.template_name,
            {'leccion': leccion, 'form': forms.RespuestaLeccionForm()},
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        leccion = self.get_leccion(pk)
        form = forms.RespuestaLeccionForm(request.POST)
        context = {'leccion': leccion, 'form': form}

        if form.is_valid():
            # Solo evalúa la respuesta; no registra intentos ni progreso.
            context['respuesta_enviada'] = True
            context['es_correcta'] = (
                form.cleaned_data['respuesta'] == bool(leccion.es_verdad)
            )
        else:
            return render(request, self.template_name, context, status=400)

        return render(request, self.template_name, context)


class CursosModuloListView(ListView):
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


class CursosModuloCreateView(CreateView):
    model = Modulo
    form_class = forms.ModuloForm
    template_name = 'APP/admin/modulos/form.html'
    success_url = reverse_lazy('cursos_modulo_list')

class CursosModuloUpdateView(UpdateView):
    model = Modulo
    form_class = forms.ModuloForm
    template_name = 'APP/admin/modulos/form.html'
    success_url = reverse_lazy('cursos_modulo_list')

class CursosModuloDeleteView(DeleteView):
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






class CursosLeccionListView(ListView):
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


class CursosLeccionCreateView(CreateView):
    model = Leccion
    form_class = forms.LeccionForm
    template_name = 'APP/admin/lecciones/form.html'
    success_url = reverse_lazy('cursos_leccion_list')

class CursosLeccionUpdateView(UpdateView):
    model = Leccion
    form_class = forms.LeccionForm
    template_name = 'APP/admin/lecciones/form.html'
    success_url = reverse_lazy('cursos_leccion_list')

class CursosLeccionDeleteView(DeleteView):
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


class RolListView(ListView):
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


class RolCreateView(CreateView):
    model = Rol
    form_class = forms.RolForm
    template_name = 'APP/admin/roles/form.html'
    success_url = reverse_lazy('rol_list')


class RolUpdateView(UpdateView):
    model = Rol
    form_class = forms.RolForm
    template_name = 'APP/admin/roles/form.html'
    success_url = reverse_lazy('rol_list')


class RolDeleteView(DeleteView):
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
    