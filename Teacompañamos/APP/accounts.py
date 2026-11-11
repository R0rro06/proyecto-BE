"""Sincronización de la cuenta de Django con el perfil de aprendizaje."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction

from .models import Perfil, Rol, Usuario


@transaction.atomic
def create_account(usuario, password):
    account = get_user_model().objects.create_user(
        username=usuario.username, email=usuario.email or '', password=password,
    )
    usuario.django_user = account
    usuario.password = make_password(None)
    usuario.save()
    return usuario


@transaction.atomic
def update_account(usuario, password=None):
    account = usuario.django_user
    account.username = usuario.username
    account.email = usuario.email or ''
    fields = ['username', 'email']
    if password:
        account.set_password(password)
        fields.append('password')
    account.save(update_fields=fields)
    usuario.save(update_fields=['username', 'email'])
    return usuario


@transaction.atomic
def delete_account(usuario):
    account = usuario.django_user
    usuario.delete()
    if account is not None:
        account.delete()


def is_primary_admin(user):
    return (
        user.is_authenticated and user.is_active and user.is_staff
        and user.is_superuser and user.username == 'admin'
    )


def ensure_admin_learning_user(user):
    """Vincula la cuenta principal del administrador con el perfil de aprendizaje."""
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
