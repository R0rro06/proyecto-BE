from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from .admin_forms import UsuarioChangeAdminForm, UsuarioCreationAdminForm
from .models import Usuario


admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'tipo_usuario')
    search_fields = ('username', 'email')
    ordering = ('username',)
    actions = None  # Evita el borrado masivo sin revisar perfiles asociados.

    @admin.display(description='Tipo')
    def tipo_usuario(self, obj):
        perfil = obj.perfil_set.select_related('rol').order_by('pk').first()
        return perfil.rol.nombre if perfil else 'Sin perfil'

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (obj is None or not obj.django_user_id)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or not obj.django_user_id)

    @method_decorator(sensitive_post_parameters(
        'password1', 'password2', 'new_password1', 'new_password2',
    ))
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_form(self, request, obj=None, change=False, **kwargs):
        kwargs['form'] = UsuarioChangeAdminForm if obj else UsuarioCreationAdminForm
        return super().get_form(request, obj, change, **kwargs)

    def save_model(self, request, obj, form, change):
        if change and not form.cleaned_data.get('new_password1'):
            # Un formulario antiguo no debe restaurar un hash ya actualizado.
            obj.save(update_fields=('username', 'email'))
        else:
            super().save_model(request, obj, form, change)
