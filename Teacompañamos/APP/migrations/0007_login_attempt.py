from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('APP', '0006_nombres_admin')]

    operations = [
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('key', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('failures', models.PositiveSmallIntegerField(default=0)),
                ('blocked_until', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'login_attempt'},
        ),
    ]
