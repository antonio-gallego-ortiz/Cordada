from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import (
    BootstrapPasswordChangeForm,
    BootstrapPasswordResetForm,
    BootstrapSetPasswordForm,
    LoginForm,
)

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
    # Recuperación de contraseña por correo electrónico.
    path(
        "contrasena/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            form_class=BootstrapPasswordResetForm,
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "contrasena/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "contrasena/restablecer/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            form_class=BootstrapSetPasswordForm,
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "contrasena/completado/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    # Cambio de contraseña con sesión iniciada.
    path(
        "contrasena/cambiar/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            form_class=BootstrapPasswordChangeForm,
            success_url=reverse_lazy("password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "contrasena/cambiada/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path("perfil/", views.profile, name="profile"),
    path("perfil/editar/", views.profile_edit, name="profile_edit"),
    path("perfil/eliminar/", views.account_delete, name="account_delete"),
    path("usuario/<str:username>/", views.public_profile, name="public_profile"),
]
