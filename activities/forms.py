from django import forms
from django.db.models import Q
from django.utils import timezone

from accounts.forms import BootstrapFormMixin

from .models import Activity, extract_first_trackpoint


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
            "distance_km",
            "elevation_gain_m",
            "duration_hours",
            "equipment",
            "gpx_file",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "equipment": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Botas de montaña, 2 L de agua, cortavientos, frontal...",
                }
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

    def clean_max_participants(self):
        value = self.cleaned_data["max_participants"]
        if self.instance.pk:
            registered = self.instance.registrations.count()
            if value < registered:
                raise forms.ValidationError(
                    f"Ya hay {registered} personas inscritas: el máximo "
                    "no puede ser menor."
                )
        return value

    def save(self, commit=True):
        activity = super().save(commit=False)
        # El parte meteorológico necesita coordenadas: se toman del primer
        # punto del track GPX.
        if activity.gpx_file:
            point = extract_first_trackpoint(activity.gpx_file)
            if point:
                activity.latitude, activity.longitude = point
        if commit:
            activity.save()
        return activity


class ActivitySearchForm(BootstrapFormMixin, forms.Form):
    """Búsqueda y filtrado del listado de actividades (RF-09)."""

    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Título o ubicación..."}),
    )
    difficulty = forms.ChoiceField(
        label="Dificultad",
        required=False,
        choices=[("", "Todas")] + list(Activity.Difficulty.choices),
    )
    date_from = forms.DateField(
        label="Desde",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        label="Hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    include_past = forms.BooleanField(label="Incluir actividades pasadas", required=False)

    def filter_queryset(self, queryset):
        """Aplica los filtros del formulario sobre el queryset de actividades."""
        data = self.cleaned_data
        if not data.get("include_past"):
            queryset = queryset.filter(date__gte=timezone.now())
        if data.get("q"):
            queryset = queryset.filter(
                Q(title__icontains=data["q"]) | Q(location__icontains=data["q"])
            )
        if data.get("difficulty"):
            queryset = queryset.filter(difficulty=data["difficulty"])
        if data.get("date_from"):
            queryset = queryset.filter(date__date__gte=data["date_from"])
        if data.get("date_to"):
            queryset = queryset.filter(date__date__lte=data["date_to"])
        return queryset
