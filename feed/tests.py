from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Follow, Post, PostComment, PostLike

User = get_user_model()


def create_user(username, **extra):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="montana-segura-99",
        **extra,
    )


class PostTests(TestCase):
    """Publicaciones del feed: creación, likes, comentarios y borrado."""

    def setUp(self):
        self.author = create_user("autora")
        self.reader = create_user("lectora")
        self.post = Post.objects.create(
            author=self.author, content="¡Cumbre en el Aneto!"
        )

    def test_feed_is_home_and_shows_posts(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "¡Cumbre en el Aneto!")

    def test_anonymous_user_cannot_publish(self):
        response = self.client.post(
            reverse("post_create"), {"content": "spam anónimo"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Post.objects.count(), 1)

    def test_user_can_publish(self):
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse("post_create"), {"content": "Primera vía de la temporada."}
        )
        self.assertRedirects(response, reverse("feed"))
        self.assertTrue(
            Post.objects.filter(author=self.reader, content__icontains="vía").exists()
        )

    def test_like_toggle(self):
        self.client.force_login(self.reader)
        url = reverse("post_like_toggle", args=[self.post.pk])
        data = self.client.post(url).json()
        self.assertEqual(data, {"liked": True, "count": 1})
        data = self.client.post(url).json()
        self.assertEqual(data, {"liked": False, "count": 0})

    def test_duplicate_like_is_impossible(self):
        PostLike.objects.create(post=self.post, user=self.reader)
        self.client.force_login(self.reader)
        self.client.post(reverse("post_like_toggle", args=[self.post.pk]))
        self.assertEqual(self.post.like_count, 0)

    def test_user_can_comment(self):
        self.client.force_login(self.reader)
        self.client.post(
            reverse("post_comment", args=[self.post.pk]),
            {"content": "¡Qué envidia!", "next": "/"},
        )
        self.assertEqual(self.post.comment_count, 1)

    def test_only_author_or_admin_can_delete_post(self):
        self.client.force_login(self.reader)
        response = self.client.post(reverse("post_delete", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)

        admin = create_user("admin", is_staff=True)
        self.client.force_login(admin)
        self.client.post(reverse("post_delete", args=[self.post.pk]))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_comment_delete_by_author(self):
        comment = PostComment.objects.create(
            post=self.post, author=self.reader, content="borrable"
        )
        self.client.force_login(self.reader)
        self.client.post(reverse("comment_delete", args=[comment.pk]), {"next": "/"})
        self.assertFalse(PostComment.objects.filter(pk=comment.pk).exists())


class FollowTests(TestCase):
    """Seguimiento entre usuarios."""

    def setUp(self):
        self.ana = create_user("ana")
        self.luis = create_user("luis")

    def toggle(self, username):
        return self.client.post(reverse("follow_toggle", args=[username]))

    def test_follow_and_unfollow(self):
        self.client.force_login(self.ana)
        self.toggle("luis")
        self.assertTrue(
            Follow.objects.filter(follower=self.ana, followed=self.luis).exists()
        )
        self.toggle("luis")
        self.assertFalse(
            Follow.objects.filter(follower=self.ana, followed=self.luis).exists()
        )

    def test_cannot_follow_self(self):
        self.client.force_login(self.ana)
        self.toggle("ana")
        self.assertEqual(Follow.objects.count(), 0)

    def test_following_filter_shows_only_followed_authors(self):
        Post.objects.create(author=self.ana, content="Post de Ana")
        Post.objects.create(author=self.luis, content="Post de Luis")
        Follow.objects.create(follower=self.ana, followed=self.luis)
        self.client.force_login(self.ana)
        response = self.client.get(f"{reverse('feed')}?siguiendo=1")
        self.assertContains(response, "Post de Luis")
        self.assertNotContains(response, "Post de Ana")
