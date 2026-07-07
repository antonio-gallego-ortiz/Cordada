from django.contrib import admin

from .models import Conversation, Listing, MarketMessage


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "seller",
        "category",
        "offer_type",
        "price",
        "status",
        "created_at",
    )
    list_filter = ("category", "offer_type", "status", "condition")
    search_fields = ("title", "description", "location")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("listing", "buyer", "created_at")


@admin.register(MarketMessage)
class MarketMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "content", "created_at")
    search_fields = ("content",)
