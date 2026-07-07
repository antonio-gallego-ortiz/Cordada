from django.urls import path

from . import views

urlpatterns = [
    path("", views.activity_list, name="activity_list"),
    path("actividades/nueva/", views.activity_create, name="activity_create"),
    path("actividades/<int:pk>/", views.activity_detail, name="activity_detail"),
    path("actividades/<int:pk>/editar/", views.activity_edit, name="activity_edit"),
    path(
        "actividades/<int:pk>/eliminar/",
        views.activity_delete,
        name="activity_delete",
    ),
]
