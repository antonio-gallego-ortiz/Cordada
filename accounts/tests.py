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
            "accept_privacy": "on",
        }
        data.update(overrides)
        return data

    def test_register_requires_privacy_consent(self):
        data = self.register_data()
        del data["accept_privacy"]
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="montanera").exists())
        self.assertContains(response, "política de privacidad")

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse("register"), self.register_data())
        self.assertRedirects(response, reverse("feed"))
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
        self.assertRedirects(response, reverse("feed"))
        self.assertFalse(User.objects.filter(username="ana").exists())

    def test_public_profile_is_visible(self):
        User.objects.create_user("ana", "ana@example.com", "montana-segura-99")
        response = self.client.get(reverse("public_profile", args=["ana"]))
        self.assertEqual(response.status_code, 200)


class PasswordFlowTests(TestCase):
    """Recuperación y cambio de contraseña."""

    def setUp(self):
        self.user = User.objects.create_user(
            "ana", "ana@example.com", "montana-segura-99"
        )

    def test_password_reset_sends_email_with_valid_link(self):
        from django.core import mail

        response = self.client.post(
            reverse("password_reset"), {"email": "ana@example.com"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Restablecer", mail.outbox[0].subject)
        self.assertIn("/cuenta/contrasena/restablecer/", mail.outbox[0].body)

    def test_unknown_email_does_not_reveal_accounts(self):
        from django.core import mail

        response = self.client.post(
            reverse("password_reset"), {"email": "nadie@example.com"}
        )
        # Misma respuesta que con un email válido: no se filtra si existe.
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_logged_user_can_change_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "montana-segura-99",
                "new_password1": "otra-clave-segura-42",
                "new_password2": "otra-clave-segura-42",
            },
        )
        self.assertRedirects(response, reverse("password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("otra-clave-segura-42"))


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
