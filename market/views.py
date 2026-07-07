from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import ListingForm, ListingSearchForm
from .models import Conversation, Listing, MarketMessage


def listing_list(request):
    """Escaparate del mercado con búsqueda y filtros."""
    form = ListingSearchForm(request.GET)
    listings = Listing.objects.filter(status=Listing.Status.AVAILABLE).select_related(
        "seller"
    )
    if form.is_valid():
        listings = form.filter_queryset(listings)
    return render(
        request, "market/listing_list.html", {"listings": listings, "form": form}
    )


def listing_detail(request, pk):
    """Detalle de un anuncio."""
    listing = get_object_or_404(Listing.objects.select_related("seller"), pk=pk)
    conversation = None
    if request.user.is_authenticated and request.user != listing.seller:
        conversation = listing.conversations.filter(buyer=request.user).first()
    return render(
        request,
        "market/listing_detail.html",
        {"listing": listing, "conversation": conversation},
    )


@login_required
def listing_create(request):
    """Publicación de un anuncio."""
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            messages.success(request, "Anuncio publicado correctamente.")
            return redirect(listing)
    else:
        form = ListingForm()
    return render(
        request,
        "market/listing_form.html",
        {"form": form, "title": "Publicar anuncio"},
    )


def get_listing_for_seller(request, pk):
    """Devuelve el anuncio solo si el usuario actual es su vendedor."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user:
        raise PermissionDenied
    return listing


@login_required
def listing_edit(request, pk):
    """Edición de un anuncio. Solo el vendedor."""
    listing = get_listing_for_seller(request, pk)
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, "Anuncio actualizado.")
            return redirect(listing)
    else:
        form = ListingForm(instance=listing)
    return render(
        request,
        "market/listing_form.html",
        {"form": form, "title": "Editar anuncio", "listing": listing},
    )


@login_required
def listing_delete(request, pk):
    """Eliminación de un anuncio: el vendedor o un administrador (moderación)."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user and not request.user.is_admin:
        raise PermissionDenied
    if request.method == "POST":
        listing.delete()
        messages.info(request, "El anuncio se ha eliminado.")
        return redirect("listing_list")
    return render(
        request, "market/listing_confirm_delete.html", {"listing": listing}
    )


@login_required
@require_POST
def listing_set_status(request, pk):
    """Cambio de estado del anuncio (disponible/reservado/cerrado). Solo el vendedor."""
    listing = get_listing_for_seller(request, pk)
    new_status = request.POST.get("status")
    if new_status in Listing.Status.values:
        listing.status = new_status
        listing.save()
        messages.success(
            request, f"El anuncio ahora está: {listing.get_status_display().lower()}."
        )
    return redirect(listing)


@login_required
def my_market(request):
    """Panel del usuario: sus anuncios y sus conversaciones."""
    my_listings = request.user.listings.all()
    conversations = (
        Conversation.objects.filter(buyer=request.user)
        | Conversation.objects.filter(listing__seller=request.user)
    )
    conversations = (
        conversations.select_related("listing", "listing__seller", "buyer")
        .annotate(last_message_at=Max("messages__created_at"))
        .order_by("-last_message_at", "-created_at")
        .distinct()
    )
    return render(
        request,
        "market/my_market.html",
        {"my_listings": my_listings, "conversations": conversations},
    )


@login_required
@require_POST
def conversation_start(request, pk):
    """Abre (o recupera) la conversación del usuario con el vendedor."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller == request.user:
        messages.error(request, "No puedes abrir un chat contigo mismo.")
        return redirect(listing)
    conversation, _ = Conversation.objects.get_or_create(
        listing=listing, buyer=request.user
    )
    return redirect("conversation_detail", pk=conversation.pk)


def get_conversation_for_participant(request, pk):
    """Devuelve la conversación solo si el usuario participa en ella."""
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "listing__seller", "buyer"),
        pk=pk,
    )
    if not conversation.is_participant(request.user):
        raise PermissionDenied
    return conversation


@login_required
def conversation_detail(request, pk):
    """Página del chat de una conversación."""
    conversation = get_conversation_for_participant(request, pk)
    return render(
        request,
        "market/conversation_detail.html",
        {
            "conversation": conversation,
            "listing": conversation.listing,
            "other_user": conversation.other_user(request.user),
        },
    )


@login_required
@require_GET
def conversation_messages(request, pk):
    """Mensajes de la conversación en JSON (para el refresco automático)."""
    conversation = get_conversation_for_participant(request, pk)
    messages_qs = conversation.messages.select_related("sender")[:200]
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
def conversation_send(request, pk):
    """Envío de un mensaje a la conversación."""
    conversation = get_conversation_for_participant(request, pk)
    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "El mensaje no puede estar vacío."}, status=400)
    if len(content) > 1000:
        return JsonResponse(
            {"error": "El mensaje no puede superar los 1000 caracteres."}, status=400
        )
    MarketMessage.objects.create(
        conversation=conversation, sender=request.user, content=content
    )
    return JsonResponse({"ok": True}, status=201)
