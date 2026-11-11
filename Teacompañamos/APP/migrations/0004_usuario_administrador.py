from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def crear_rol_administrador(apps, schema_editor):
    Rol = apps.get_model('APP', 'Rol')
    Rol.objects.get_or_create(
        codigo='administrador',
        defaults={'nombre': 'Administrador', 'descripcion': 'Gestiona módulos, lecciones y roles'},
    )


class Migration(migrations.Migration):
    dependencies = [
        ('APP', '0003_registro_y_roles'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario', name='django_user',
            field=models.OneToOneField(
                to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                blank=True, null=True, editable=False,
            ),
        ),
        migrations.AlterField(
            model_name='usuario', name='email',
            field=models.CharField(max_length=150, unique=True, blank=True, null=True),
        ),
        migrations.RunPython(crear_rol_administrador, migrations.RunPython.noop),
    ]
