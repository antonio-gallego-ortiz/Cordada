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
            "gpx_file",
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

    def clean_gpx_file(self):
        gpx_file = self.cleaned_data.get("gpx_file")
        if gpx_file and gpx_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "El archivo GPX no puede superar los 5 MB."
            )
        return gpx_file
