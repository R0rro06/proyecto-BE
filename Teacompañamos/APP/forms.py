from django import forms
from .models import Leccion, Modulo, Estado, Perfil, Progreso, Rol, Usuario

class LeccionForm(forms.ModelForm):
    # Muestra opciones legibles y conserva los valores 1/0 del modelo.
    es_verdad = forms.TypedChoiceField(
        choices=((1, 'Verdadero'), (0, 'Falso')),
        coerce=int,
        label='Respuesta correcta',
    )

    class Meta:
        model = Leccion
        fields = ('pregunta', 'es_verdad', 'explicacion', 'modulo')
        

class RespuestaLeccionForm(forms.Form):
    # Convierte la opción enviada a bool para compararla con Leccion.es_verdad.
    respuesta = forms.TypedChoiceField(
        choices=(('1', 'Verdadero'), ('0', 'Falso')),
        coerce=lambda value: value == '1',
        widget=forms.RadioSelect,
        label='Elige tu respuesta',
    )


class ModuloForm(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = '__all__'


class EstadoForm(forms.ModelForm):
    class Meta:
        model = Estado
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