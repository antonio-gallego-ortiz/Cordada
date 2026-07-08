from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cordada.pagination import paginate

from .forms import PostForm
from .models import Follow, Post, PostComment, PostLike

User = get_user_model()


def feed(request):
    """Página de inicio: el feed social de la comunidad."""
    posts = Post.objects.select_related("author").prefetch_related(
        "comments__author", "likes"
    )
    following_only = request.GET.get("siguiendo") == "1"
    if following_only and request.user.is_authenticated:
        followed_ids = request.user.following.values_list("followed_id", flat=True)
        posts = posts.filter(author_id__in=followed_ids)
    page_obj, querystring = paginate(request, posts, per_page=10)
    posts = list(page_obj.object_list)
    if request.user.is_authenticated:
        liked_ids = set(
            PostLike.objects.filter(
                user=request.user, post__in=posts
            ).values_list("post_id", flat=True)
        )
        for post in posts:
            post.is_liked_by_user = post.pk in liked_ids
    form = PostForm() if request.user.is_authenticated else None
    return render(
        request,
        "feed/feed.html",
        {
            "posts": posts,
            "page_obj": page_obj,
            "querystring": querystring,
            "form": form,
            "following_only": following_only,
        },
    )


@login_required
@require_POST
def post_create(request):
    """Publicación de un post en el feed."""
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "¡Publicado!")
    else:
        messages.error(request, "La publicación no puede estar vacía.")
    return redirect("feed")


@login_required
@require_POST
def post_delete(request, pk):
    """Eliminación de un post: su autor o un administrador (moderación)."""
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user and not request.user.is_admin:
        raise PermissionDenied
    post.delete()
    messages.info(request, "Publicación eliminada.")
    return redirect("feed")


@login_required
@require_POST
def post_like_toggle(request, pk):
    """Alterna el me gusta del usuario en un post. Responde JSON."""
    post = get_object_or_404(Post, pk=pk)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    return JsonResponse({"liked": created, "count": post.like_count})


@login_required
@require_POST
def post_comment(request, pk):
    """Añade un comentario a un post."""
    post = get_object_or_404(Post, pk=pk)
    content = request.POST.get("content", "").strip()
    if content:
        PostComment.objects.create(post=post, author=request.user, content=content)
    return redirect(f"{request.POST.get('next', '/')}#post-{post.pk}")


@login_required
@require_POST
def comment_delete(request, pk):
    """Eliminación de un comentario: su autor o un administrador."""
    comment = get_object_or_404(PostComment, pk=pk)
    if comment.author != request.user and not request.user.is_admin:
        raise PermissionDenied
    post_pk = comment.post_id
    comment.delete()
    return redirect(f"{request.POST.get('next', '/')}#post-{post_pk}")


@login_required
@require_POST
def follow_toggle(request, username):
    """Alterna el seguimiento del usuario indicado."""
    target = get_object_or_404(User, username=username, is_active=True)
    if target == request.user:
        messages.error(request, "No puedes seguirte a ti mismo.")
        return redirect("public_profile", username=username)
    follow, created = Follow.objects.get_or_create(
        follower=request.user, followed=target
    )
    if not created:
        follow.delete()
        messages.info(request, f"Has dejado de seguir a {target}.")
    else:
        messages.success(request, f"Ahora sigues a {target}.")
    return redirect("public_profile", username=username)
