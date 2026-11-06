from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class ProjectAdminSite(AdminSite):
    def has_permission(self, request):
        user = request.user
        return (
            user.is_authenticated and user.is_active and user.is_staff
            and user.is_superuser and user.username == 'admin'
        )


class ProjectAdminConfig(AdminConfig):
    default_site = 'Teacompañamos.admin_config.ProjectAdminSite'
