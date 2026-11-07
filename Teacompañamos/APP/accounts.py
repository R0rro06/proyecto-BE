"""Sincronización de la cuenta de Django con el perfil de aprendizaje."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction


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
