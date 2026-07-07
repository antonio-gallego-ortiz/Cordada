from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path("registro/", views.register, name="register"),
    path(
        "entrar/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html", authentication_form=LoginForm
        ),
        name="login",
    ),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("perfil/", views.profile, name="profile"),
    path("perfil/editar/", views.profile_edit, name="profile_edit"),
    path("perfil/eliminar/", views.account_delete, name="account_delete"),
    path("usuario/<str:username>/", views.public_profile, name="public_profile"),
]
