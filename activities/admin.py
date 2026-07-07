from django.contrib import admin

from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "difficulty", "location", "organizer")
    list_filter = ("difficulty", "date")
    search_fields = ("title", "location")
