from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
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
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_activities",
        verbose_name="organizador",
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
