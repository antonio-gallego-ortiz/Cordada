from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Activity, Registration, register_user_for_activity

User = get_user_model()


def create_user(username):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="montana-segura-99",
    )


def create_activity(organizer, **kwargs):
    defaults = {
        "title": "Subida al Mulhacén",
        "description": "Ruta clásica desde Capileira.",
        "date": timezone.now() + timedelta(days=7),
        "difficulty": Activity.Difficulty.HARD,
        "location": "Sierra Nevada",
        "meeting_point": "Aparcamiento de Capileira",
        "max_participants": 2,
        "organizer": organizer,
    }
    defaults.update(kwargs)
    return Activity.objects.create(**defaults)


class RegistrationRulesTests(TestCase):
    """Reglas de negocio de las inscripciones (RF-05, RF-06)."""

    def setUp(self):
        self.organizer = create_user("organizadora")
        self.member = create_user("montanera")
        self.activity = create_activity(self.organizer)

    def test_user_can_register(self):
        registration = register_user_for_activity(self.member, self.activity.pk)
        self.assertEqual(registration.activity, self.activity)
        self.assertEqual(self.activity.participants_count, 1)

    def test_user_cannot_register_twice(self):
        register_user_for_activity(self.member, self.activity.pk)
        with self.assertRaises(ValidationError):
            register_user_for_activity(self.member, self.activity.pk)
        self.assertEqual(self.activity.participants_count, 1)

    def test_cannot_exceed_max_participants(self):
        register_user_for_activity(create_user("ana"), self.activity.pk)
        register_user_for_activity(create_user("luis"), self.activity.pk)
        self.assertTrue(self.activity.is_full)
        with self.assertRaises(ValidationError):
            register_user_for_activity(self.member, self.activity.pk)
        self.assertEqual(self.activity.participants_count, 2)

    def test_cannot_register_in_past_activity(self):
        past = create_activity(
            self.organizer, date=timezone.now() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            register_user_for_activity(self.member, past.pk)

    def test_organizer_cannot_register_in_own_activity(self):
        with self.assertRaises(ValidationError):
            register_user_for_activity(self.organizer, self.activity.pk)

    def test_user_can_cancel_registration(self):
        register_user_for_activity(self.member, self.activity.pk)
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("registration_cancel", args=[self.activity.pk])
        )
        self.assertRedirects(
            response, reverse("activity_detail", args=[self.activity.pk])
        )
        self.assertFalse(
            Registration.objects.filter(
                user=self.member, activity=self.activity
            ).exists()
        )

    def test_anonymous_user_cannot_register(self):
        response = self.client.post(
            reverse("registration_create", args=[self.activity.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(self.activity.participants_count, 0)


class ActivityPermissionTests(TestCase):
    """Permisos del CRUD de actividades (RF-04, RF-10)."""

    def setUp(self):
        self.organizer = create_user("organizadora")
        self.other = create_user("intrusa")
        self.activity = create_activity(self.organizer)

    def test_anonymous_user_cannot_create_activity(self):
        response = self.client.get(reverse("activity_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_only_organizer_can_edit(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("activity_edit", args=[self.activity.pk]))
        self.assertEqual(response.status_code, 403)

    def test_only_organizer_can_delete(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("activity_delete", args=[self.activity.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Activity.objects.filter(pk=self.activity.pk).exists())

    def test_organizer_can_delete(self):
        self.client.force_login(self.organizer)
        response = self.client.post(
            reverse("activity_delete", args=[self.activity.pk])
        )
        self.assertRedirects(response, reverse("activity_list"))
        self.assertFalse(Activity.objects.filter(pk=self.activity.pk).exists())
