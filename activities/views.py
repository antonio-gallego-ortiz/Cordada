from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ActivityForm
from .models import Activity, Registration, register_user_for_activity


def activity_list(request):
    """Listado de actividades futuras (portada)."""
    activities = Activity.objects.filter(date__gte=timezone.now()).select_related(
        "organizer"
    )
    return render(
        request, "activities/activity_list.html", {"activities": activities}
    )


def activity_detail(request, pk):
    """Detalle de una actividad con sus participantes."""
    activity = get_object_or_404(
        Activity.objects.select_related("organizer"), pk=pk
    )
    registrations = activity.registrations.select_related("user")
    return render(
        request,
        "activities/activity_detail.html",
        {
            "activity": activity,
            "registrations": registrations,
            "user_is_registered": activity.is_user_registered(request.user),
        },
    )


@login_required
def activity_create(request):
    """Creación de una actividad (RF-03). Solo usuarios autenticados."""
    if request.method == "POST":
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.organizer = request.user
            activity.save()
            messages.success(request, "Actividad creada correctamente.")
            return redirect(activity)
    else:
        form = ActivityForm()
    return render(
        request,
        "activities/activity_form.html",
        {"form": form, "title": "Nueva actividad"},
    )


def get_activity_for_organizer(request, pk):
    """Devuelve la actividad solo si el usuario actual es su organizador."""
    activity = get_object_or_404(Activity, pk=pk)
    if activity.organizer != request.user:
        raise PermissionDenied
    return activity


@login_required
def activity_edit(request, pk):
    """Edición de una actividad. Solo el organizador (RF-04)."""
    activity = get_activity_for_organizer(request, pk)
    if request.method == "POST":
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, "Actividad actualizada correctamente.")
            return redirect(activity)
    else:
        form = ActivityForm(instance=activity)
    return render(
        request,
        "activities/activity_form.html",
        {"form": form, "title": "Editar actividad", "activity": activity},
    )


@login_required
def activity_delete(request, pk):
    """Eliminación de una actividad. Solo el organizador (RF-04)."""
    activity = get_activity_for_organizer(request, pk)
    if request.method == "POST":
        activity.delete()
        messages.info(request, "La actividad se ha eliminado.")
        return redirect("activity_list")
    return render(
        request, "activities/activity_confirm_delete.html", {"activity": activity}
    )


@login_required
@require_POST
def registration_create(request, pk):
    """Inscripción en una actividad (RF-05, RF-06)."""
    get_object_or_404(Activity, pk=pk)
    try:
        register_user_for_activity(request.user, pk)
    except ValidationError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, "¡Inscripción realizada! Nos vemos en la montaña.")
    return redirect("activity_detail", pk=pk)


@login_required
@require_POST
def registration_cancel(request, pk):
    """Cancelación de la inscripción propia (RF-05)."""
    activity = get_object_or_404(Activity, pk=pk)
    deleted, _ = Registration.objects.filter(
        user=request.user, activity=activity
    ).delete()
    if deleted:
        messages.info(request, "Has cancelado tu inscripción.")
    else:
        messages.error(request, "No estabas inscrito/a en esta actividad.")
    return redirect("activity_detail", pk=pk)


@login_required
def my_activities(request):
    """Actividades en las que participa u organiza el usuario (RF-05)."""
    registered = (
        Activity.objects.filter(registrations__user=request.user)
        .select_related("organizer")
    )
    organized = request.user.organized_activities.select_related("organizer")
    return render(
        request,
        "activities/my_activities.html",
        {"registered": registered, "organized": organized},
    )
