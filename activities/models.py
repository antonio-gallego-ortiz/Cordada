from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone


class Activity(models.Model):
    """Actividad de montaña organizada por un usuario."""

    class Difficulty(models.TextChoices):
        EASY = "easy", "Fácil"
        MODERATE = "moderate", "Moderada"
        HARD = "hard", "Difícil"
        VERY_HARD = "very_hard", "Muy difícil"

    title = models.CharField("título", max_length=120)
    description = models.TextField("descripción")
    date = models.DateTimeField("fecha y hora")
    difficulty = models.CharField(
        "dificultad", max_length=20, choices=Difficulty.choices
    )
    location = models.CharField("ubicación", max_length=150)
    meeting_point = models.CharField("punto de encuentro", max_length=150)
    max_participants = models.PositiveIntegerField(
        "número máximo de participantes", validators=[MinValueValidator(1)]
    )
    equipment = models.TextField(
        "material necesario",
        blank=True,
        help_text="Material recomendado para la ruta: calzado, agua, crampones...",
    )
    distance_km = models.DecimalField(
        "distancia (km)", max_digits=5, decimal_places=1, null=True, blank=True
    )
    elevation_gain_m = models.PositiveIntegerField(
        "desnivel positivo (m)", null=True, blank=True
    )
    duration_hours = models.DecimalField(
        "duración estimada (horas)",
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_activities",
        verbose_name="organizador",
    )
    gpx_file = models.FileField(
        "archivo GPX",
        upload_to="gpx/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["gpx"])],
    )
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        ordering = ["date"]
        verbose_name = "actividad"
        verbose_name_plural = "actividades"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("activity_detail", args=[self.pk])

    @property
    def is_past(self):
        return self.date < timezone.now()

    @property
    def participants_count(self):
        return self.registrations.count()

    @property
    def free_places(self):
        return self.max_participants - self.participants_count

    @property
    def is_full(self):
        return self.free_places <= 0

    def is_user_registered(self, user):
        if not user.is_authenticated:
            return False
        return self.registrations.filter(user=user).exists()

    def can_chat(self, user):
        """El chat es solo para el organizador y los inscritos."""
        if not user.is_authenticated:
            return False
        return self.organizer_id == user.pk or self.is_user_registered(user)


class Registration(models.Model):
    """Inscripción de un usuario en una actividad."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="usuario",
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="actividad",
    )
    created_at = models.DateTimeField("fecha de inscripción", auto_now_add=True)

    class Meta:
        constraints = [
            # Un usuario no puede inscribirse dos veces a la misma actividad.
            models.UniqueConstraint(
                fields=["user", "activity"], name="unique_user_activity"
            )
        ]
        ordering = ["created_at"]
        verbose_name = "inscripción"
        verbose_name_plural = "inscripciones"

    def __str__(self):
        return f"{self.user} → {self.activity}"


class ActivityPhoto(models.Model):
    """Fotografía de la ruta: vías de ascensión, pasos clave, paisajes..."""

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="actividad",
    )
    image = models.ImageField("imagen", upload_to="activity_photos/")
    caption = models.CharField("pie de foto", max_length=150, blank=True)
    created_at = models.DateTimeField("fecha de subida", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "foto de la actividad"
        verbose_name_plural = "fotos de la actividad"

    def __str__(self):
        return f"Foto de {self.activity}"


class ActivityMessage(models.Model):
    """Mensaje del chat de una actividad (solo organizador e inscritos)."""

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="actividad",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_messages",
        verbose_name="usuario",
    )
    content = models.TextField("mensaje", max_length=1000)
    created_at = models.DateTimeField("fecha de envío", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "mensaje de actividad"
        verbose_name_plural = "mensajes de actividad"

    def __str__(self):
        return f"{self.user} en {self.activity}: {self.content[:40]}"


def register_user_for_activity(user, activity_pk):
    """Inscribe a un usuario en una actividad aplicando las reglas de negocio.

    Se ejecuta dentro de una transacción con bloqueo de fila para que dos
    inscripciones simultáneas no puedan superar el límite de plazas.
    Lanza ``ValidationError`` si la inscripción no es válida.
    """
    with transaction.atomic():
        activity = Activity.objects.select_for_update().get(pk=activity_pk)
        if activity.is_past:
            raise ValidationError("No puedes apuntarte a una actividad ya celebrada.")
        if activity.organizer_id == user.pk:
            raise ValidationError("Eres el organizador de esta actividad.")
        if activity.registrations.filter(user=user).exists():
            raise ValidationError("Ya estás inscrito/a en esta actividad.")
        if activity.is_full:
            raise ValidationError("No quedan plazas libres en esta actividad.")
        return Registration.objects.create(user=user, activity=activity)
