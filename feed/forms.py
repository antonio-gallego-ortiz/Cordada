from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Post


class PostForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Post
        fields = ["content"]
        labels = {"content": ""}
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "¿Qué has hecho este fin de semana? Comparte tu experiencia...",
                }
            ),
        }
