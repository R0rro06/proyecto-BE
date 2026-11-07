from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from .admin_forms import UsuarioChangeAdminForm, UsuarioCreationAdminForm
from .accounts import create_account, delete_account, update_account
from .models import Perfil, Progreso, Rol, Usuario


admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'tipo_usuario')
    search_fields = ('username', 'email')
    list_filter = ('perfil__rol',)
    ordering = ('username',)
    actions = None  # Evita el borrado masivo sin revisar perfiles asociados.

    @admin.display(description='Tipo')
    def tipo_usuario(self, obj):
        perfil = obj.perfil_set.select_related('rol').order_by('pk').first()
        return perfil.rol.nombre if perfil else 'Sin perfil'

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (obj is None or obj.username != 'admin')

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or obj.username != 'admin')

    @method_decorator(sensitive_post_parameters(
        'password1', 'password2', 'new_password1', 'new_password2',
    ))
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_form(self, request, obj=None, change=False, **kwargs):
        kwargs['form'] = UsuarioChangeAdminForm if obj else UsuarioCreationAdminForm
        return super().get_form(request, obj, change, **kwargs)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                update_account(obj, form.cleaned_data.get('new_password1'))
            else:
                create_account(obj, form.cleaned_data['password1'])
            rol = Rol.objects.get(codigo=form.cleaned_data['tipo'])
            Perfil.objects.update_or_create(usuario=obj, defaults={'rol': rol})

    def delete_model(self, request, obj):
        delete_account(obj)

    def get_deleted_objects(self, objs, request):
        # La baja de un usuario elimina sus perfiles y avances por CASCADE.
        # Esos modelos siguen protegidos contra el borrado directo en el Admin.
        deleted, counts, permissions, protected = super().get_deleted_objects(objs, request)
        cascade_names = {Perfil._meta.verbose_name, Progreso._meta.verbose_name}
        return deleted, counts, permissions - cascade_names, protected


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre')
    search_fields = ('codigo', 'nombre')
    actions = None

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (
            obj is None or (not obj.codigo and not obj.perfil_set.exists())
        )


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'rol')
    list_filter = ('rol',)
    search_fields = ('usuario__username',)
    readonly_fields = ('usuario',)

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (
            obj is None or obj.usuario.username != 'admin'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'rol':
            kwargs['queryset'] = Rol.objects.exclude(codigo='administrador')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
