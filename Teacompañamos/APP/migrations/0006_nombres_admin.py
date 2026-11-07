from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('APP', '0005_unify_user_auth')]

    operations = [
        migrations.AlterModelOptions(
            name='perfil',
            options={'managed': True, 'db_table': 'perfil', 'verbose_name': 'perfil',
                     'verbose_name_plural': 'Perfiles'},
        ),
        migrations.AlterModelOptions(
            name='rol',
            options={'managed': True, 'db_table': 'rol', 'verbose_name': 'rol',
                     'verbose_name_plural': 'Roles'},
        ),
    ]
