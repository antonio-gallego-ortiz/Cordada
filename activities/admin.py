from django.contrib import admin

from .models import Activity, Registration


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "difficulty", "location", "organizer")
    list_filter = ("difficulty", "date")
    search_fields = ("title", "location")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "activity", "created_at")
    list_filter = ("created_at",)
