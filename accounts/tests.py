from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import UserSport

User = get_user_model()


class AccountTests(TestCase):
    """Gestión de usuarios (RF-01, RF-02)."""

    def register_data(self, **overrides):
        data = {
            "username": "montanera",
            "first_name": "María",
            "last_name": "García",
            "email": "maria@example.com",
            "password1": "montana-segura-99",
            "password2": "montana-segura-99",
        }
        data.update(overrides)
        return data

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse("register"), self.register_data())
        self.assertRedirects(response, reverse("activity_list"))
        user = User.objects.get(username="montanera")
        self.assertEqual(user.email, "maria@example.com")
        # La contraseña se guarda hasheada, nunca en claro.
        self.assertNotEqual(user.password, "montana-segura-99")
        self.assertTrue(user.check_password("montana-segura-99"))
        # El usuario queda autenticado tras registrarse.
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

    def test_duplicate_email_is_rejected(self):
        self.client.post(reverse("register"), self.register_data())
        self.client.logout()
        response = self.client.post(
            reverse("register"), self.register_data(username="otra")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="otra").exists())

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_profile_edit_updates_data(self):
        user = User.objects.create_user(
            "ana", "ana@example.com", "montana-segura-99"
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Ana",
                "last_name": "López",
                "email": "ana@example.com",
                "bio": "Me encanta el senderismo.",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        user.refresh_from_db()
        self.assertEqual(user.bio, "Me encanta el senderismo.")

    def test_account_delete_removes_user(self):
        user = User.objects.create_user(
            "ana", "ana@example.com", "montana-segura-99"
        )
        self.client.force_login(user)
        response = self.client.post(reverse("account_delete"))
        self.assertRedirects(response, reverse("activity_list"))
        self.assertFalse(User.objects.filter(username="ana").exists())

    def test_public_profile_is_visible(self):
        User.objects.create_user("ana", "ana@example.com", "montana-segura-99")
        response = self.client.get(reverse("public_profile", args=["ana"]))
        self.assertEqual(response.status_code, 200)


class UserSportTests(TestCase):
    """Deportes y niveles del perfil."""

    def setUp(self):
        self.user = User.objects.create_user(
            "ana", "ana@example.com", "montana-segura-99", first_name="Ana"
        )
        self.client.force_login(self.user)

    def edit_profile(self, **sports):
        data = {"first_name": "Ana", "last_name": "López", "email": "ana@example.com"}
        data.update(sports)
        return self.client.post(reverse("profile_edit"), data)

    def test_user_can_set_sports_with_level(self):
        response = self.edit_profile(
            sport_hiking="advanced", sport_climbing="beginner"
        )
        self.assertRedirects(response, reverse("profile"))
        levels = dict(self.user.sports.values_list("sport", "level"))
        self.assertEqual(
            levels, {"hiking": "advanced", "climbing": "beginner"}
        )

    def test_clearing_a_sport_removes_it(self):
        UserSport.objects.create(user=self.user, sport="skiing", level="expert")
        self.edit_profile(sport_skiing="")
        self.assertFalse(self.user.sports.filter(sport="skiing").exists())

    def test_sports_are_shown_in_public_profile(self):
        UserSport.objects.create(user=self.user, sport="hiking", level="expert")
        self.client.logout()
        response = self.client.get(reverse("public_profile", args=["ana"]))
        self.assertContains(response, "Senderismo")
        self.assertContains(response, "Experto")
