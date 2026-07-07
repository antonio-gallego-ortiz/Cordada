from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserSport


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Perfil de Cordada", {"fields": ("photo", "bio")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff")


@admin.register(UserSport)
class UserSportAdmin(admin.ModelAdmin):
    list_display = ("user", "sport", "level")
    list_filter = ("sport", "level")
