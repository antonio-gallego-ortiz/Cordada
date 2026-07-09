from django.urls import path

from . import views

urlpatterns = [
    path("", views.listing_list, name="listing_list"),
    path("publicar/", views.listing_create, name="listing_create"),
    path("anuncio/<int:pk>/", views.listing_detail, name="listing_detail"),
    path("anuncio/<int:pk>/editar/", views.listing_edit, name="listing_edit"),
    path("anuncio/<int:pk>/eliminar/", views.listing_delete, name="listing_delete"),
    path("anuncio/<int:pk>/estado/", views.listing_set_status, name="listing_set_status"),
    path("imagen/<int:pk>/eliminar/", views.listing_image_delete, name="listing_image_delete"),
    path("anuncio/<int:pk>/contactar/", views.conversation_start, name="conversation_start"),
    path("conversaciones/", views.my_conversations, name="my_conversations"),
    path("mis-anuncios/", views.my_listings, name="my_listings"),
    path("chat/<int:pk>/", views.conversation_detail, name="conversation_detail"),
    path("chat/<int:pk>/mensajes/", views.conversation_messages, name="conversation_messages"),
    path("chat/<int:pk>/enviar/", views.conversation_send, name="conversation_send"),
]
