from django.contrib import admin

from .models import Community, CommunityMessage, Membership


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name", "description")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "community", "joined_at")


@admin.register(CommunityMessage)
class CommunityMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "community", "content", "created_at")
    search_fields = ("content",)
