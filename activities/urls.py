from django.urls import path

from . import views

urlpatterns = [
    path("actividades/", views.activity_list, name="activity_list"),
    path("actividades/nueva/", views.activity_create, name="activity_create"),
    path("actividades/<int:pk>/", views.activity_detail, name="activity_detail"),
    path("actividades/<int:pk>/editar/", views.activity_edit, name="activity_edit"),
    path(
        "actividades/<int:pk>/eliminar/",
        views.activity_delete,
        name="activity_delete",
    ),
    path(
        "actividades/<int:pk>/apuntarse/",
        views.registration_create,
        name="registration_create",
    ),
    path(
        "actividades/<int:pk>/desapuntarse/",
        views.registration_cancel,
        name="registration_cancel",
    ),
    path(
        "actividades/<int:pk>/fotos/",
        views.activity_photo_add,
        name="activity_photo_add",
    ),
    path(
        "fotos/<int:pk>/eliminar/",
        views.activity_photo_delete,
        name="activity_photo_delete",
    ),
    path(
        "actividades/<int:pk>/chat/mensajes/",
        views.chat_messages,
        name="chat_messages",
    ),
    path(
        "actividades/<int:pk>/chat/enviar/",
        views.chat_send,
        name="chat_send",
    ),
    path("mis-actividades/", views.my_activities, name="my_activities"),
]
