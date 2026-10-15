from django import forms
from .models import CursosLeccion, CursosModulo, Estado, Leccion, Modulo, Perfil, Progreso, Rol, Usuario

class LeccionForm(forms.ModelForm):
    class Meta:
        model = Leccion
        fields = '__all__'
        

class ModuloForm(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = ('pregunta', 'es_verdad', 'explicacion')


class EstadoForm(forms.ModelForm):
    class Meta:
        model = Estado
        fields = '__all__'

class LeccionForm(forms.ModelForm):
    class Meta:
        model = Leccion
        fields = '__all__'

class ModuloForm(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = '__all__'

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = '__all__'

class ProgresoForm(forms.ModelForm):
    class Meta:
        model = Progreso
        fields = '__all__'

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = '__all__'

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'