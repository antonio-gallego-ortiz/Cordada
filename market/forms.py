from django import forms
from django.db.models import Q

from accounts.forms import BootstrapFormMixin

from .models import Listing


class ListingForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "title",
            "description",
            "category",
            "condition",
            "offer_type",
            "price",
            "location",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "title": forms.TextInput(
                attrs={"placeholder": "Ej.: Botas Sportiva Trango del 42"}
            ),
            "location": forms.TextInput(attrs={"placeholder": "Ej.: Granada"}),
        }

    def clean(self):
        cleaned = super().clean()
        offer_type = cleaned.get("offer_type")
        price = cleaned.get("price")
        if offer_type == Listing.OfferType.LOAN:
            cleaned["price"] = None
        elif price is None:
            self.add_error(
                "price", "Indica el precio (o elige préstamo gratuito)."
            )
        return cleaned


class ListingSearchForm(BootstrapFormMixin, forms.Form):
    """Búsqueda y filtrado del mercado."""

    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "¿Qué material buscas?"}),
    )
    category = forms.ChoiceField(
        label="Categoría",
        required=False,
        choices=[("", "Todas")] + list(Listing.Category.choices),
    )
    offer_type = forms.ChoiceField(
        label="Tipo",
        required=False,
        choices=[("", "Todos")] + list(Listing.OfferType.choices),
    )
    max_price = forms.DecimalField(
        label="Precio máx. (€)",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"placeholder": "Sin límite"}),
    )

    def filter_queryset(self, queryset):
        data = self.cleaned_data
        if data.get("q"):
            queryset = queryset.filter(
                Q(title__icontains=data["q"]) | Q(description__icontains=data["q"])
            )
        if data.get("category"):
            queryset = queryset.filter(category=data["category"])
        if data.get("offer_type"):
            queryset = queryset.filter(offer_type=data["offer_type"])
        if data.get("max_price") is not None:
            queryset = queryset.filter(price__lte=data["max_price"])
        return queryset
