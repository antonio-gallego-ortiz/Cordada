from django.contrib import admin

from .models import Follow, Post, PostComment, PostLike


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "content", "created_at")
    search_fields = ("content",)
    list_filter = ("created_at",)


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "content", "created_at")
    search_fields = ("content",)


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed", "created_at")
