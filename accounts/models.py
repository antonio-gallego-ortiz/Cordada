from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario de la plataforma.

    Extiende el usuario de Django (username, first_name, last_name, email,
    password, date_joined) con los campos propios de Cordada. El rol de
    administrador se apoya en el campo estándar ``is_staff``.
    """

    email = models.EmailField("correo electrónico", unique=True)
    photo = models.ImageField(
        "fotografía", upload_to="profile_photos/", blank=True, null=True
    )
    bio = models.TextField("biografía", max_length=500, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        """Rol de administrador (moderación de la plataforma)."""
        return self.is_staff
