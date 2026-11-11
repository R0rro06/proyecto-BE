"""Vincula usuarios anteriores a Django Auth sin cambiar sus perfiles ni progreso."""

import unicodedata

from django.conf import settings
from django.contrib.auth.hashers import identify_hasher, make_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import migrations, transaction


def forwards(apps, schema_editor):
    alias = schema_editor.connection.alias
    Usuario = apps.get_model('APP', 'Usuario')
    auth_app, auth_model = settings.AUTH_USER_MODEL.split('.')
    Account = apps.get_model(auth_app, auth_model)
    pending = list(Usuario.objects.using(alias).filter(django_user__isnull=True).order_by('pk'))
    existing = {unicodedata.normalize('NFKC', name).casefold()
                for name in Account.objects.using(alias).values_list('username', flat=True)}
    validator = UnicodeUsernameValidator()
    for usuario in pending:
        normalized = unicodedata.normalize('NFKC', usuario.username)
        key = normalized.casefold()
        if key == 'admin' or key in existing or len(normalized) > 150:
            raise RuntimeError(f'Usuario {usuario.pk}: nombre duplicado o reservado; migración cancelada.')
        validator(normalized)
        existing.add(key)
        if len(usuario.password) > 128:
            raise RuntimeError(f'Usuario {usuario.pk}: hash demasiado largo; migración cancelada.')
        try:
            identify_hasher(usuario.password)
        except ValueError as error:
            raise RuntimeError(f'Usuario {usuario.pk}: hash incompatible; migración cancelada.') from error
    with transaction.atomic(using=alias):
        for usuario in pending:
            account = Account.objects.using(alias).create(
                username=usuario.username, email=usuario.email or '',
                password=usuario.password, is_active=True, is_staff=False, is_superuser=False,
            )
            usuario.django_user_id = account.pk
            usuario.password = make_password(None)
            usuario.save(using=alias, update_fields=['django_user', 'password'])


class Migration(migrations.Migration):
    dependencies = [
        ('APP', '0004_usuario_administrador'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [migrations.RunPython(forwards)]
