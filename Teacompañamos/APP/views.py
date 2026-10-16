from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views import View

from . import forms
from .models import Leccion, Modulo, Usuario
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy


class PanelAdminView(TemplateView):
    template_name = 'APP/panel_admin.html'


class DashboardView(TemplateView):
    template_name = 'APP/dashboard.html'

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
    template_name = 'APP/aprender_modulo.html'

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
    template_name = 'APP/responder_leccion.html'

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
            context['respuesta_enviada'] = True
            context['es_correcta'] = (
                form.cleaned_data['respuesta'] == bool(leccion.es_verdad)
            )
        else:
            return render(request, self.template_name, context, status=400)

        return render(request, self.template_name, context)


class CursosModuloListView(ListView):
    model = Modulo
    template_name = 'APP/cursos_modulo_list.html'
    context_object_name = 'modulos'

class CursosModuloCreateView(CreateView):
    model = Modulo
    form_class = forms.ModuloForm
    template_name = 'APP/cursos_modulo_form.html'
    success_url = reverse_lazy('cursos_modulo_list')

class CursosModuloUpdateView(UpdateView):
    model = Modulo
    form_class = forms.ModuloForm
    template_name = 'APP/cursos_modulo_form.html'
    success_url = reverse_lazy('cursos_modulo_list')

class CursosModuloDeleteView(DeleteView):
    model = Modulo
    template_name = 'APP/cursos_modulo_confirm_delete.html'
    success_url = reverse_lazy('cursos_modulo_list')

    def form_valid(self, form):
        if self.object.leccion_set.exists():
            messages.error(
                self.request,
                'No se puede eliminar el módulo mientras tenga lecciones. '
                'Elimina o mueve sus lecciones primero.',
            )
            return redirect('cursos_modulo_list')
        return super().form_valid(form)






class CursosLeccionListView(ListView):
    model = Leccion
    template_name = 'APP/cursos_leccion_list.html'
    context_object_name = 'lecciones'

class CursosLeccionCreateView(CreateView):
    model = Leccion
    form_class = forms.LeccionForm
    template_name = 'APP/cursos_leccion_form.html'
    success_url = reverse_lazy('cursos_leccion_list')

class CursosLeccionUpdateView(UpdateView):
    model = Leccion
    form_class = forms.LeccionForm
    template_name = 'APP/cursos_leccion_form.html'
    success_url = reverse_lazy('cursos_leccion_list')

class CursosLeccionDeleteView(DeleteView):
    model = Leccion
    template_name = 'APP/cursos_leccion_confirm_delete.html'
    success_url = reverse_lazy('cursos_leccion_list')

    def form_valid(self, form):
        if self.object.progreso_set.exists():
            messages.error(
                self.request,
                'No se puede eliminar la lección mientras tenga progreso asociado.',
            )
            return redirect('cursos_leccion_list')
        return super().form_valid(form)
    