
# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Leccion(models.Model):
    id = models.BigAutoField(primary_key=True)
    pregunta = models.CharField(max_length=300)
    es_verdad = models.IntegerField()
    explicacion = models.TextField()
    completada = models.IntegerField(default=0)
    modulo = models.ForeignKey('Modulo', models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'leccion'


class Modulo(models.Model):
    id = models.BigAutoField(primary_key=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    orden = models.PositiveIntegerField()
    def __str__(self):
        return f"Módulo {self.orden}: {self.titulo}"

    class Meta:
        managed = True
        db_table = 'modulo'


class Estado(models.Model):
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = 'estado'



class Perfil(models.Model):
    usuario = models.ForeignKey('Usuario', models.DO_NOTHING)
    rol = models.ForeignKey('Rol', models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'perfil'


class Progreso(models.Model):
    perfil = models.ForeignKey(Perfil, models.DO_NOTHING)
    leccion = models.ForeignKey(Leccion, models.DO_NOTHING)
    estado = models.ForeignKey(Estado, models.DO_NOTHING, blank=True, null=True)
    intentos = models.IntegerField()
    fecha_completada = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'progreso'


class Rol(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'rol'


class Usuario(models.Model):
    username = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    password = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'usuario'
