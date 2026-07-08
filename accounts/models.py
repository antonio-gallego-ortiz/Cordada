from django.contrib.auth.models import AbstractUser
from django.db import models

from cordada.validators import validate_upload_size


class User(AbstractUser):
    """Usuario de la plataforma.

    Extiende el usuario de Django (username, first_name, last_name, email,
    password, date_joined) con los campos propios de Cordada. El rol de
    administrador se apoya en el campo estándar ``is_staff``.
    """

    email = models.EmailField("correo electrónico", unique=True)
    photo = models.ImageField(
        "fotografía",
        upload_to="profile_photos/",
        blank=True,
        null=True,
        validators=[validate_upload_size],
    )
    bio = models.TextField("biografía", max_length=500, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        """Rol de administrador (moderación de la plataforma)."""
        return self.is_staff


class UserSport(models.Model):
    """Deporte de montaña que practica un usuario, con su nivel."""

    class Sport(models.TextChoices):
        HIKING = "hiking", "Senderismo"
        MOUNTAINEERING = "mountaineering", "Alpinismo"
        CLIMBING = "climbing", "Escalada"
        SKIING = "skiing", "Esquí"
        SNOWBOARDING = "snowboarding", "Snowboard"
        TRAIL_RUNNING = "trail_running", "Trail running"
        MTB = "mtb", "Bici de montaña"
        CANYONING = "canyoning", "Barranquismo"

    class Level(models.TextChoices):
        BEGINNER = "beginner", "Principiante"
        INTERMEDIATE = "intermediate", "Intermedio"
        ADVANCED = "advanced", "Avanzado"
        EXPERT = "expert", "Experto"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sports",
        verbose_name="usuario",
    )
    sport = models.CharField("deporte", max_length=20, choices=Sport.choices)
    level = models.CharField("nivel", max_length=20, choices=Level.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "sport"], name="unique_user_sport")
        ]
        ordering = ["sport"]
        verbose_name = "deporte del usuario"
        verbose_name_plural = "deportes del usuario"

    def __str__(self):
        return f"{self.user} — {self.get_sport_display()} ({self.get_level_display()})"
