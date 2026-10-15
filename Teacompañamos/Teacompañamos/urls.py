"""
URL configuration for Teacompañamos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from APP import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('modulos/', views.CursosModuloListView.as_view(), name='cursos_modulo_list'),
    path('modulos/create/', views.CursosModuloCreateView.as_view(), name='cursos_modulo_form'),
    path('modulos/<int:pk>/update/', views.CursosModuloUpdateView.as_view(), name='cursos_modulo_update'),
    path('modulos/<int:pk>/delete/', views.CursosModuloDeleteView.as_view(), name='cursos_modulo_delete'),
]
