from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import ActivityForm, ActivitySearchForm
from .models import (
    Activity,
    ActivityMessage,
    Registration,
    register_user_for_activity,
)


def activity_list(request):
    """Listado de actividades con búsqueda y filtros (RF-09)."""
    form = ActivitySearchForm(request.GET)
    activities = Activity.objects.select_related("organizer")
    if form.is_valid():
        activities = form.filter_queryset(activities)
    else:
        activities = activities.filter(date__gte=timezone.now())
    return render(
        request,
        "activities/activity_list.html",
        {"activities": activities, "form": form},
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
            "user_can_chat": activity.can_chat(request.user),
        },
    )


@login_required
def activity_create(request):
    """Creación de una actividad (RF-03). Solo usuarios autenticados."""
    if request.method == "POST":
        form = ActivityForm(request.POST, request.FILES)
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
        form = ActivityForm(request.POST, request.FILES, instance=activity)
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
    """Eliminación de una actividad.

    Puede eliminarla su organizador (RF-04) o un administrador como
    labor de moderación (RF-10).
    """
    activity = get_object_or_404(Activity, pk=pk)
    if activity.organizer != request.user and not request.user.is_admin:
        raise PermissionDenied
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


def get_activity_for_chat(request, pk):
    """Devuelve la actividad solo si el usuario puede usar su chat."""
    activity = get_object_or_404(Activity, pk=pk)
    if not activity.can_chat(request.user):
        raise PermissionDenied
    return activity


@login_required
@require_GET
def chat_messages(request, pk):
    """Mensajes del chat de la actividad en JSON (para el refresco automático)."""
    activity = get_activity_for_chat(request, pk)
    messages_qs = activity.messages.select_related("user")[:200]
    return JsonResponse(
        {
            "messages": [
                {
                    "id": message.pk,
                    "author": message.user.get_full_name() or message.user.username,
                    "initial": (message.user.first_name or message.user.username)[:1].upper(),
                    "mine": message.user_id == request.user.pk,
                    "content": message.content,
                    "created": timezone.localtime(message.created_at).strftime(
                        "%d/%m %H:%M"
                    ),
                }
                for message in messages_qs
            ]
        }
    )


@login_required
@require_POST
def chat_send(request, pk):
    """Envío de un mensaje al chat de la actividad."""
    activity = get_activity_for_chat(request, pk)
    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "El mensaje no puede estar vacío."}, status=400)
    if len(content) > 1000:
        return JsonResponse(
            {"error": "El mensaje no puede superar los 1000 caracteres."}, status=400
        )
    ActivityMessage.objects.create(
        activity=activity, user=request.user, content=content
    )
    return JsonResponse({"ok": True}, status=201)


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
