from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm, RegisterForm, SportsForm

User = get_user_model()


def register(request):
    """Registro de un nuevo usuario (RF-01)."""
    if request.user.is_authenticated:
        return redirect("feed")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "¡Bienvenido/a a Cordada! Tu cuenta se ha creado correctamente.")
            return redirect("feed")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    """Perfil propio del usuario autenticado."""
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit(request):
    """Edición del perfil propio, incluidos deportes y niveles (RF-02)."""
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        sports_form = SportsForm(request.POST, user=request.user)
        if form.is_valid() and sports_form.is_valid():
            form.save()
            sports_form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
        sports_form = SportsForm(user=request.user)
    return render(
        request,
        "accounts/profile_edit.html",
        {"form": form, "sports_form": sports_form},
    )


@login_required
def account_delete(request):
    """Baja de la cuenta: elimina el usuario y sus datos (RGPD)."""
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.info(request, "Tu cuenta se ha eliminado. ¡Esperamos verte de nuevo en la montaña!")
        return redirect("feed")
    return render(request, "accounts/account_delete.html")


def public_profile(request, username):
    """Perfil público de cualquier usuario, con su estado de seguimiento."""
    from feed.models import Follow

    profile_user = get_object_or_404(User, username=username, is_active=True)
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user, followed=profile_user
        ).exists()
    return render(
        request,
        "accounts/public_profile.html",
        {"profile_user": profile_user, "is_following": is_following},
    )
