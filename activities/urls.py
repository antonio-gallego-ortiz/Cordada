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
    path("mis-actividades/", views.my_activities, name="my_activities"),
]
