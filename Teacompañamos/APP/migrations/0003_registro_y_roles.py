from django.db import migrations, models


TIPOS = (
    ('estudiante', 'Estudiante'),
    ('familiar', 'Familiar'),
    ('profesor', 'Profesor'),
    ('otro', 'Otro'),
)


def crear_roles(apps, schema_editor):
    Rol = apps.get_model('APP', 'Rol')
    for codigo, nombre in TIPOS:
        rol = Rol.objects.filter(nombre__iexact=nombre).order_by('pk').first()
        if rol is None:
            Rol.objects.create(codigo=codigo, nombre=nombre)
        elif not rol.codigo:
            rol.codigo = codigo
            rol.save(update_fields=('codigo',))


class Migration(migrations.Migration):
    dependencies = [('APP', '0002_permitir_borrar_usuario_con_avance')]

    operations = [
        migrations.AddField(
            model_name='rol', name='codigo',
            field=models.CharField(max_length=20, unique=True, blank=True, null=True, editable=False),
        ),
        migrations.RunPython(crear_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='usuario', name='username',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='usuario', name='email',
            field=models.CharField(max_length=150, unique=True),
        ),
    ]
