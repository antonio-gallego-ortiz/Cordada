from django.urls import path

from . import views

urlpatterns = [
    path("", views.feed, name="feed"),
    path("publicar/", views.post_create, name="post_create"),
    path("publicacion/<int:pk>/eliminar/", views.post_delete, name="post_delete"),
    path("publicacion/<int:pk>/like/", views.post_like_toggle, name="post_like_toggle"),
    path("publicacion/<int:pk>/comentar/", views.post_comment, name="post_comment"),
    path("comentario/<int:pk>/eliminar/", views.comment_delete, name="comment_delete"),
    path("usuario/<str:username>/seguir/", views.follow_toggle, name="follow_toggle"),
]
