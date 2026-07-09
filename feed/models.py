from django.conf import settings
from django.db import models

from cordada.validators import validate_upload_size


class Post(models.Model):
    """Publicación del feed social: experiencias, rutas, fotos..."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="autor",
    )
    content = models.TextField("contenido", max_length=3000)
    created_at = models.DateTimeField("fecha de publicación", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "publicación"
        verbose_name_plural = "publicaciones"

    def __str__(self):
        return f"{self.author}: {self.content[:50]}"

    @property
    def like_count(self):
        # len() sobre .all() aprovecha la caché de prefetch_related en el
        # feed y evita una consulta COUNT por publicación.
        return len(self.likes.all())

    @property
    def comment_count(self):
        return len(self.comments.all())

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


class PostImage(models.Model):
    """Imagen de una publicación (una publicación puede llevar varias)."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="publicación",
    )
    image = models.ImageField(
        "imagen", upload_to="posts/", validators=[validate_upload_size]
    )

    class Meta:
        ordering = ["pk"]
        verbose_name = "imagen de publicación"
        verbose_name_plural = "imágenes de publicación"

    def __str__(self):
        return f"Imagen de {self.post}"


class PostLike(models.Model):
    """Me gusta de un usuario en una publicación."""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes", verbose_name="publicación"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
        verbose_name="usuario",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Un usuario solo puede dar un me gusta por publicación.
            models.UniqueConstraint(fields=["post", "user"], name="unique_post_like")
        ]
        verbose_name = "me gusta"
        verbose_name_plural = "me gusta"

    def __str__(self):
        return f"{self.user} → {self.post}"


class PostComment(models.Model):
    """Comentario en una publicación."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="publicación",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_comments",
        verbose_name="autor",
    )
    content = models.TextField("comentario", max_length=1000)
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"

    def __str__(self):
        return f"{self.author}: {self.content[:40]}"


class Follow(models.Model):
    """Relación de seguimiento entre usuarios."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="seguidor",
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="seguido",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followed"], name="unique_follow"
            ),
            # Nadie puede seguirse a sí mismo.
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("followed")),
                name="no_self_follow",
            ),
        ]
        verbose_name = "seguimiento"
        verbose_name_plural = "seguimientos"

    def __str__(self):
        return f"{self.follower} sigue a {self.followed}"
