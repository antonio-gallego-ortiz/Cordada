from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Listing(models.Model):
    """Anuncio de material de montaña de segunda mano."""

    class Category(models.TextChoices):
        FOOTWEAR = "footwear", "Calzado"
        CLOTHING = "clothing", "Ropa técnica"
        CLIMBING = "climbing", "Escalada"
        SNOW = "snow", "Esquí y snowboard"
        CAMPING = "camping", "Acampada y vivac"
        BACKPACKS = "backpacks", "Mochilas"
        ELECTRONICS = "electronics", "Electrónica y GPS"
        OTHER = "other", "Otros"

    class Condition(models.TextChoices):
        NEW = "new", "Nuevo (sin estrenar)"
        LIKE_NEW = "like_new", "Como nuevo"
        GOOD = "good", "Buen estado"
        USED = "used", "Usado"

    class OfferType(models.TextChoices):
        SALE = "sale", "Venta"
        RENT = "rent", "Alquiler (por día)"
        LOAN = "loan", "Préstamo gratuito"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        RESERVED = "reserved", "Reservado"
        CLOSED = "closed", "Vendido / entregado"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
        verbose_name="vendedor",
    )
    title = models.CharField("título", max_length=120)
    description = models.TextField("descripción")
    category = models.CharField("categoría", max_length=20, choices=Category.choices)
    condition = models.CharField(
        "estado del artículo", max_length=20, choices=Condition.choices
    )
    offer_type = models.CharField(
        "tipo de oferta",
        max_length=10,
        choices=OfferType.choices,
        default=OfferType.SALE,
    )
    price = models.DecimalField(
        "precio (€)",
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="En alquileres, precio por día. En préstamos se deja vacío.",
    )
    photo = models.ImageField(
        "fotografía", upload_to="listings/", blank=True, null=True
    )
    location = models.CharField("localidad", max_length=100)
    status = models.CharField(
        "estado del anuncio",
        max_length=10,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    created_at = models.DateTimeField("fecha de publicación", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "anuncio"
        verbose_name_plural = "anuncios"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("listing_detail", args=[self.pk])

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def price_label(self):
        """Precio formateado según el tipo de oferta."""
        if self.offer_type == self.OfferType.LOAN:
            return "Gratis"
        if self.price is None:
            return "A convenir"
        amount = f"{self.price:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        if self.offer_type == self.OfferType.RENT:
            return f"{amount} €/día"
        return f"{amount} €"


class Conversation(models.Model):
    """Conversación privada entre un interesado y el vendedor de un anuncio."""

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="conversations",
        verbose_name="anuncio",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="market_conversations",
        verbose_name="interesado",
    )
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        constraints = [
            # Un interesado solo tiene una conversación por anuncio.
            models.UniqueConstraint(
                fields=["listing", "buyer"], name="unique_listing_buyer"
            )
        ]
        ordering = ["-created_at"]
        verbose_name = "conversación"
        verbose_name_plural = "conversaciones"

    def __str__(self):
        return f"{self.buyer} ↔ {self.listing.seller} · {self.listing}"

    def is_participant(self, user):
        if not user.is_authenticated:
            return False
        return user.pk in (self.buyer_id, self.listing.seller_id)

    def other_user(self, user):
        """El otro participante de la conversación."""
        return self.listing.seller if user.pk == self.buyer_id else self.buyer


class MarketMessage(models.Model):
    """Mensaje dentro de una conversación del mercado."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="conversación",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="market_messages",
        verbose_name="remitente",
    )
    content = models.TextField("mensaje", max_length=1000)
    created_at = models.DateTimeField("fecha de envío", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "mensaje del mercado"
        verbose_name_plural = "mensajes del mercado"

    def __str__(self):
        return f"{self.sender}: {self.content[:40]}"
