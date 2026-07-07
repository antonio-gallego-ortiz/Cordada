from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import CommunityForm
from .models import Community, CommunityMessage, Membership


def community_list(request):
    """Listado de comunidades con su número de miembros."""
    communities = Community.objects.annotate(members_total=Count("memberships"))
    my_community_ids = set()
    if request.user.is_authenticated:
        my_community_ids = set(
            request.user.community_memberships.values_list("community_id", flat=True)
        )
    return render(
        request,
        "communities/community_list.html",
        {"communities": communities, "my_community_ids": my_community_ids},
    )


@login_required
def community_create(request):
    """Creación de una comunidad. El creador se une automáticamente."""
    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()
            Membership.objects.create(community=community, user=request.user)
            messages.success(request, "Comunidad creada. ¡Ya eres su primer miembro!")
            return redirect(community)
    else:
        form = CommunityForm()
    return render(request, "communities/community_form.html", {"form": form})


def community_detail(request, pk):
    """Detalle de la comunidad: chat de grupo y miembros."""
    community = get_object_or_404(
        Community.objects.select_related("created_by"), pk=pk
    )
    memberships = community.memberships.select_related("user")
    return render(
        request,
        "communities/community_detail.html",
        {
            "community": community,
            "memberships": memberships,
            "user_is_member": community.is_member(request.user),
        },
    )


@login_required
@require_POST
def community_join(request, pk):
    """Incorporación a una comunidad."""
    community = get_object_or_404(Community, pk=pk)
    Membership.objects.get_or_create(community=community, user=request.user)
    messages.success(request, f"Te has unido a {community.name}.")
    return redirect(community)


@login_required
@require_POST
def community_leave(request, pk):
    """Salida de una comunidad."""
    community = get_object_or_404(Community, pk=pk)
    Membership.objects.filter(community=community, user=request.user).delete()
    messages.info(request, f"Has salido de {community.name}.")
    return redirect(community)


@login_required
def community_delete(request, pk):
    """Eliminación de una comunidad: su creador o un administrador."""
    community = get_object_or_404(Community, pk=pk)
    if community.created_by != request.user and not request.user.is_admin:
        raise PermissionDenied
    if request.method == "POST":
        community.delete()
        messages.info(request, "La comunidad se ha eliminado.")
        return redirect("community_list")
    return render(
        request, "communities/community_confirm_delete.html", {"community": community}
    )


def get_community_for_member(request, pk):
    """Devuelve la comunidad solo si el usuario es miembro."""
    community = get_object_or_404(Community, pk=pk)
    if not community.is_member(request.user):
        raise PermissionDenied
    return community


@login_required
@require_GET
def community_messages(request, pk):
    """Mensajes del chat de grupo en JSON (para el refresco automático)."""
    community = get_community_for_member(request, pk)
    messages_qs = community.messages.select_related("sender")[:200]
    return JsonResponse(
        {
            "messages": [
                {
                    "id": message.pk,
                    "author": message.sender.get_full_name()
                    or message.sender.username,
                    "initial": (message.sender.first_name or message.sender.username)[
                        :1
                    ].upper(),
                    "mine": message.sender_id == request.user.pk,
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
def community_send(request, pk):
    """Envío de un mensaje al chat de grupo."""
    community = get_community_for_member(request, pk)
    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "El mensaje no puede estar vacío."}, status=400)
    if len(content) > 1000:
        return JsonResponse(
            {"error": "El mensaje no puede superar los 1000 caracteres."}, status=400
        )
    CommunityMessage.objects.create(
        community=community, sender=request.user, content=content
    )
    return JsonResponse({"ok": True}, status=201)
