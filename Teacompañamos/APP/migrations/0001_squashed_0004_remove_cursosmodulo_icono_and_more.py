from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [
        ('APP', '0001_initial'),
        ('APP', '0002_alter_cursosleccion_options_and_more'),
        ('APP', '0003_cursosleccion_modulo_leccion_modulo_perfil_rol_and_more'),
        ('APP', '0004_remove_cursosmodulo_icono_and_more'),
    ]

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CursosModulo',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=200)),
                ('descripcion', models.TextField()),
                ('orden', models.PositiveIntegerField()),
            ],
            options={
                'db_table': 'cursos_modulo',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='CursosLeccion',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('pregunta', models.CharField(max_length=300)),
                ('es_verdad', models.IntegerField()),
                ('explicacion', models.TextField()),
                ('completada', models.IntegerField(default=0)),
                (
                    'modulo',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='APP.cursosmodulo',
                    ),
                ),
            ],
            options={
                'db_table': 'cursos_leccion',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Estado',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('nombre', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'estado',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Modulo',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'pregunta',
                    models.CharField(blank=True, max_length=500, null=True),
                ),
                ('es_verdad', models.IntegerField(blank=True, null=True)),
                ('explicacion', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'modulo',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Leccion',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('titulo', models.CharField(blank=True, max_length=150, null=True)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('orden', models.IntegerField(blank=True, null=True)),
                (
                    'modulo',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='APP.modulo',
                    ),
                ),
            ],
            options={
                'db_table': 'leccion',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Rol',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('nombre', models.CharField(max_length=100)),
                (
                    'descripcion',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
            ],
            options={
                'db_table': 'rol',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('username', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=150)),
                ('password', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'usuario',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Perfil',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'rol',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='APP.rol',
                    ),
                ),
                (
                    'usuario',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='APP.usuario',
                    ),
                ),
            ],
            options={
                'db_table': 'perfil',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Progreso',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('intentos', models.IntegerField()),
                ('fecha_completada', models.DateTimeField(blank=True, null=True)),
                (
                    'estado',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='APP.estado',
                    ),
                ),
                (
                    'leccion',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='APP.leccion',
                    ),
                ),
                (
                    'perfil',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='APP.perfil',
                    ),
                ),
            ],
            options={
                'db_table': 'progreso',
                'managed': True,
            },
        ),
    ]
