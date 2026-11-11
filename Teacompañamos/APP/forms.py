from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator

from .models import Leccion, Modulo, Rol, Usuario


TIPOS_USUARIO = (
    ('estudiante', 'Estudiante'),
    ('familiar', 'Familiar'),
    ('profesor', 'Profesor'),
    ('otro', 'Otro'),
)


class UsuarioAdminBaseForm(forms.ModelForm):
    username = forms.CharField(max_length=100, label='Nombre de usuario')
    email = forms.EmailField(max_length=150, label='Correo electrónico')
    tipo = forms.ChoiceField(choices=TIPOS_USUARIO, label='Rol')

    class Meta:
        model = Usuario
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:
            perfil = self.instance.perfil_set.select_related('rol').order_by('pk').first()
            if perfil and perfil.rol.codigo in dict(self.fields['tipo'].choices):
                self.fields['tipo'].initial = perfil.rol.codigo

    def password_validation_user(self, cleaned_data):
        return get_user_model()(
            username=cleaned_data.get('username', ''),
            email=cleaned_data.get('email', ''),
        )

    def clean_username(self):
        username = get_user_model().normalize_username(self.cleaned_data['username'].strip())
        if len(username) > 100:
            raise forms.ValidationError('El nombre de usuario no puede superar 100 caracteres.')
        UnicodeUsernameValidator()(username)
        if username.casefold() == 'admin' and not self.instance.django_user_id:
            raise forms.ValidationError('Este nombre está reservado para la cuenta administradora.')
        usuarios = Usuario.objects.filter(username__iexact=username)
        cuentas = get_user_model().objects.filter(username__iexact=username)
        if self.instance.pk:
            usuarios = usuarios.exclude(pk=self.instance.pk)
            if self.instance.django_user_id:
                cuentas = cuentas.exclude(pk=self.instance.django_user_id)
        if usuarios.exists() or cuentas.exists():
            raise forms.ValidationError('Ya existe un usuario con este nombre.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        usuarios = Usuario.objects.filter(email__iexact=email)
        if self.instance.pk:
            usuarios = usuarios.exclude(pk=self.instance.pk)
        if usuarios.exists():
            raise forms.ValidationError('Ya existe un usuario con este correo.')
        return email


class UsuarioCreationAdminForm(UsuarioAdminBaseForm):
    password1 = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput, strip=False,
    )
    password2 = forms.CharField(
        label='Confirmar contraseña', widget=forms.PasswordInput, strip=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Las contraseñas no coinciden.')
            else:
                validate_password(
                    password1, user=self.password_validation_user(cleaned_data),
                )
        return cleaned_data


class UsuarioChangeAdminForm(UsuarioAdminBaseForm):
    new_password1 = forms.CharField(
        label='Nueva contraseña', widget=forms.PasswordInput, required=False,
        strip=False,
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña', widget=forms.PasswordInput, required=False,
        strip=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 or password2:
            if not password1 or password1 != password2:
                self.add_error('new_password2', 'Las contraseñas no coinciden.')
            else:
                validate_password(
                    password1, user=self.password_validation_user(cleaned_data),
                )
        return cleaned_data


class RegistroUsuarioForm(UsuarioCreationAdminForm):
    tipo = forms.ChoiceField(choices=TIPOS_USUARIO, label='Soy')


class AccesoEstudianteForm(forms.Form):
    username = forms.CharField(max_length=100, label='Nombre de usuario')
    password = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput, strip=False,
    )


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
        fields = ('titulo', 'descripcion', 'orden')

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ('nombre', 'descripcion')
