from django.urls import path

from . import views

urlpatterns = [
    path("", views.community_list, name="community_list"),
    path("crear/", views.community_create, name="community_create"),
    path("<int:pk>/", views.community_detail, name="community_detail"),
    path("<int:pk>/unirse/", views.community_join, name="community_join"),
    path("<int:pk>/salir/", views.community_leave, name="community_leave"),
    path("<int:pk>/eliminar/", views.community_delete, name="community_delete"),
    path("<int:pk>/mensajes/", views.community_messages, name="community_messages"),
    path("<int:pk>/enviar/", views.community_send, name="community_send"),
]
