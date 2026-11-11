"""Bloqueo compartido entre el acceso del sitio y el de Django Admin."""

from datetime import timedelta
from math import ceil

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import LoginAttempt


MAX_FAILURES = 5
BLOCK_SECONDS = 60


def attempt_key(request, username, *, admin=False):
    # REMOTE_ADDR lo entrega el servidor; no confiar en cabeceras X-Forwarded-For.
    address = request.META.get('REMOTE_ADDR', '')
    name = username.strip().casefold()
    subject = f'admin:{address}' if admin or name == 'admin' else f'user:{address}:{name}'
    return salted_hmac('APP.login_throttle', subject, algorithm='sha256').hexdigest()


def retry_after(key):
    blocked_until = LoginAttempt.objects.filter(pk=key).values_list('blocked_until', flat=True).first()
    if blocked_until is None:
        return 0
    return max(0, ceil((blocked_until - timezone.now()).total_seconds()))


def record_failure(key):
    with transaction.atomic():
        attempt, _ = LoginAttempt.objects.select_for_update().get_or_create(pk=key)
        now = timezone.now()
        if attempt.blocked_until and attempt.blocked_until > now:
            return max(1, ceil((attempt.blocked_until - now).total_seconds()))
        if attempt.blocked_until:
            attempt.failures = 0
            attempt.blocked_until = None
        attempt.failures += 1
        if attempt.failures >= MAX_FAILURES:
            attempt.blocked_until = now + timedelta(seconds=BLOCK_SECONDS)
        attempt.save()
        return BLOCK_SECONDS if attempt.blocked_until else 0


def clear_failures(key):
    LoginAttempt.objects.filter(pk=key).delete()


def blocked_message(seconds):
    return f'Demasiados intentos de inicio de sesión. Vuelve a intentarlo en {seconds} segundos.'
