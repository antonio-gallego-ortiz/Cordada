from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin

from .models import Activity


class ActivityForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            "title",
            "description",
            "date",
            "difficulty",
            "location",
            "meeting_point",
            "max_participants",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < timezone.now():
            raise forms.ValidationError("La fecha de la actividad debe ser futura.")
        return date
