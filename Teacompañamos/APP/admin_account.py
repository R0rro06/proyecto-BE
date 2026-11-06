"""Vincula la cuenta administrativa de Django con su perfil de aprendizaje."""

from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Perfil, Rol, Usuario


def is_primary_admin(user):
    return (
        user.is_authenticated and user.is_active and user.is_staff
        and user.is_superuser and user.username == 'admin'
    )


def ensure_admin_learning_user(user):
    if not is_primary_admin(user):
        raise ValueError('Solo la cuenta administradora puede tener este perfil.')

    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=user.pk)
        usuario = Usuario.objects.filter(django_user=user).first()
        if usuario is None:
            email = user.email or None
            if email and Usuario.objects.filter(email__iexact=email).exists():
                email = None
            usuario = Usuario.objects.create(
                django_user=user, username=user.username, email=email,
                password=make_password(None),
            )
        rol = Rol.objects.get(codigo='administrador')
        Perfil.objects.get_or_create(usuario=usuario, rol=rol)
        return usuario
