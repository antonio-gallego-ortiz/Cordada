from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User, UserSport


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


class SportsForm(BootstrapFormMixin, forms.Form):
    """Nivel del usuario en cada deporte de montaña.

    Genera un desplegable por deporte; dejarlo vacío significa que
    no lo practica.
    """

    LEVEL_CHOICES = [("", "No lo practico")] + list(UserSport.Level.choices)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        current = {}
        if user is not None:
            current = dict(user.sports.values_list("sport", "level"))
        for sport in UserSport.Sport:
            self.fields[f"sport_{sport.value}"] = forms.ChoiceField(
                label=sport.label,
                choices=self.LEVEL_CHOICES,
                required=False,
                initial=current.get(sport.value, ""),
                widget=forms.Select(attrs={"class": "form-select"}),
            )

    def save(self):
        for sport in UserSport.Sport:
            level = self.cleaned_data.get(f"sport_{sport.value}")
            if level:
                UserSport.objects.update_or_create(
                    user=self.user, sport=sport.value, defaults={"level": level}
                )
            else:
                UserSport.objects.filter(user=self.user, sport=sport.value).delete()
