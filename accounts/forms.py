from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class BootstrapFormMixin:
    """Añade las clases CSS de Bootstrap a los widgets del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            field.widget.attrs.setdefault("class", css_class)


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["first_name", "last_name", "email"]:
            self.fields[name].required = True


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "photo", "bio"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
            "photo": "Fotografía",
            "bio": "Biografía",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
