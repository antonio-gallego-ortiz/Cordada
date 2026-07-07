from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Post


class PostForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Post
        fields = ["content", "image"]
        labels = {"content": "", "image": ""}
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "¿Qué has hecho este fin de semana? Comparte tu experiencia...",
                }
            ),
            # Oculto: se abre desde el botón «Foto» del compositor.
            "image": forms.FileInput(attrs={"class": "d-none"}),
        }
