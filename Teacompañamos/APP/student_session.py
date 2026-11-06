"""Sesiones de estudiantes de APP.Usuario, separadas de django.contrib.auth.User."""

from django.utils.crypto import constant_time_compare, salted_hmac

from .admin_account import is_primary_admin
from .models import Usuario


STUDENT_ID_KEY = 'app_usuario_id'
STUDENT_HASH_KEY = 'app_usuario_auth_hash'


def _password_fingerprint(usuario):
    # Una contraseña cambiada invalida la sesión sin guardar su hash en ella.
    return salted_hmac('APP.Usuario.session', usuario.password).hexdigest()


def student_from_request(request):
    usuario_id = request.session.get(STUDENT_ID_KEY)
    fingerprint = request.session.get(STUDENT_HASH_KEY)
    if not isinstance(usuario_id, int) or not isinstance(fingerprint, str):
        return None

    usuario = Usuario.objects.filter(pk=usuario_id).first()
    if (usuario and constant_time_compare(fingerprint, _password_fingerprint(usuario))
            and (not usuario.django_user_id or (
                is_primary_admin(request.user) and request.user.pk == usuario.django_user_id
            ))):
        return usuario

    request.session.pop(STUDENT_ID_KEY, None)
    request.session.pop(STUDENT_HASH_KEY, None)
    return None


def start_student_session(request, usuario):
    request.session.cycle_key()
    request.session[STUDENT_ID_KEY] = usuario.pk
    request.session[STUDENT_HASH_KEY] = _password_fingerprint(usuario)
