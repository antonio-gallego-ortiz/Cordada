from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Community


class CommunityForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Community
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Ej.: Escaladores de Madrid"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "¿De qué va el grupo? ¿Quién debería unirse?",
                }
            ),
        }
