"""Rutas públicas, de aprendizaje y administración."""
from django.contrib import admin
from django.urls import path

from APP import views

urlpatterns = [
    path('preferencia-tema/', views.preferencia_tema, name='preferencia_tema'),
    path('cookies/', views.consentimiento_cookies, name='consentimiento_cookies'),
    path('admin/', admin.site.urls),
    path('acceso/', views.acceso_estudiante, name='acceso_estudiante'),
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('salir/', views.salir_estudiante, name='salir_estudiante'),
    # Experiencia de aprendizaje.
    path('', views.inicio, name='inicio'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('aprender/modulos/<int:pk>/', views.AprenderModuloView.as_view(), name='aprender_modulo'),
    path('aprender/lecciones/<int:pk>/', views.ResponderLeccionView.as_view(), name='responder_leccion'),
    # Panel administrativo y CRUD de módulos, lecciones y roles.
    path('panel_administracion/', views.PanelAdminView.as_view(), name='panel_administracion'),
    path('modulos/', views.CursosModuloListView.as_view(), name='cursos_modulo_list'),
    path('modulos/create/', views.CursosModuloCreateView.as_view(), name='cursos_modulo_form'),
    path('modulos/<int:pk>/update/', views.CursosModuloUpdateView.as_view(), name='cursos_modulo_update'),
    path('modulos/<int:pk>/delete/', views.CursosModuloDeleteView.as_view(), name='cursos_modulo_delete'),
    path('lecciones/', views.CursosLeccionListView.as_view(), name='cursos_leccion_list'),
    path('lecciones/create/', views.CursosLeccionCreateView.as_view(), name='cursos_leccion_form'),
    path('lecciones/<int:pk>/update/', views.CursosLeccionUpdateView.as_view(), name='cursos_leccion_update'),
    path('lecciones/<int:pk>/delete/', views.CursosLeccionDeleteView.as_view(), name='cursos_leccion_delete'),
    path('roles/', views.RolListView.as_view(), name='rol_list'),
    path('roles/create/', views.RolCreateView.as_view(), name='rol_form'),
    path('roles/<int:pk>/update/', views.RolUpdateView.as_view(), name='rol_update'),
    path('roles/<int:pk>/delete/', views.RolDeleteView.as_view(), name='rol_delete'),
]
