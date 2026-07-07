from django.conf import settings
from django.db import models
from django.urls import reverse


class Community(models.Model):
    """Comunidad o grupo de personas con intereses comunes."""

    name = models.CharField("nombre", max_length=80, unique=True)
    description = models.TextField("descripción", max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_communities",
        verbose_name="creador",
    )
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "comunidad"
        verbose_name_plural = "comunidades"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("community_detail", args=[self.pk])

    @property
    def member_count(self):
        return self.memberships.count()

    def is_member(self, user):
        if not user.is_authenticated:
            return False
        return self.memberships.filter(user=user).exists()


class Membership(models.Model):
    """Pertenencia de un usuario a una comunidad."""

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="comunidad",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_memberships",
        verbose_name="usuario",
    )
    joined_at = models.DateTimeField("fecha de incorporación", auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["community", "user"], name="unique_community_member"
            )
        ]
        ordering = ["joined_at"]
        verbose_name = "miembro"
        verbose_name_plural = "miembros"

    def __str__(self):
        return f"{self.user} en {self.community}"


class CommunityMessage(models.Model):
    """Mensaje del chat de grupo de una comunidad."""

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="comunidad",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_messages",
        verbose_name="remitente",
    )
    content = models.TextField("mensaje", max_length=1000)
    created_at = models.DateTimeField("fecha de envío", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "mensaje de comunidad"
        verbose_name_plural = "mensajes de comunidad"

    def __str__(self):
        return f"{self.sender} en {self.community}: {self.content[:40]}"
