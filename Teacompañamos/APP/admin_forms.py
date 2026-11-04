from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password

from .models import Usuario


class UsuarioAdminBaseForm(forms.ModelForm):
    email = forms.EmailField(max_length=150, label='Correo electrónico')

    class Meta:
        model = Usuario
        fields = ('username', 'email')

    def password_validation_user(self, cleaned_data):
        # ModelForm aún no ha copiado estos valores a self.instance en clean().
        return Usuario(
            username=cleaned_data.get('username', ''),
            email=cleaned_data.get('email', ''),
        )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        usuarios = Usuario.objects.filter(username__iexact=username)
        if self.instance.pk:
            usuarios = usuarios.exclude(pk=self.instance.pk)
        if usuarios.exists():
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

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.password = make_password(self.cleaned_data['password1'])
        if commit:
            usuario.save()
        return usuario


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

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('new_password1')
        if password:
            usuario.password = make_password(password)
        if commit:
            usuario.save()
        return usuario
