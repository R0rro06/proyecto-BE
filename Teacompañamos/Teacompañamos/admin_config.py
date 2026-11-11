from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.shortcuts import render
from django.urls import reverse


class ProjectAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        from APP.login_throttle import attempt_key, clear_failures, record_failure, retry_after

        if request.method != 'POST':
            return super().login(request, extra_context)

        key = attempt_key(request, request.POST.get('username', ''), admin=True)
        wait_seconds = retry_after(key)
        if wait_seconds:
            return self._blocked_login(request, wait_seconds)

        response = super().login(request, extra_context)
        if response.status_code in (301, 302, 303) and self.has_permission(request):
            clear_failures(key)
            return response

        wait_seconds = record_failure(key)
        return self._blocked_login(request, wait_seconds) if wait_seconds else response

    def _blocked_login(self, request, wait_seconds):
        from django.contrib.admin.forms import AdminAuthenticationForm
        from APP.login_throttle import blocked_message

        form = AdminAuthenticationForm(request, data={})
        form.is_valid()
        form.errors.clear()
        form.add_error(None, blocked_message(wait_seconds))
        context = {
            **self.each_context(request),
            'title': 'Iniciar sesión',
            'app_path': request.get_full_path(),
            'form': form,
            'next': request.POST.get('next') or reverse('admin:index', current_app=self.name),
        }
        request.current_app = self.name
        response = render(request, self.login_template or 'admin/login.html', context, status=429)
        response['Retry-After'] = str(wait_seconds)
        return response

    def has_permission(self, request):
        from APP.accounts import is_primary_admin

        return is_primary_admin(request.user)


class ProjectAdminConfig(AdminConfig):
    default_site = 'Teacompañamos.admin_config.ProjectAdminSite'
