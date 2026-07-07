from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ActivityForm
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


class ActivitySearchTests(TestCase):
    """Búsqueda y filtrado de actividades (RF-09)."""

    def setUp(self):
        organizer = create_user("organizadora")
        self.future_easy = create_activity(
            organizer,
            title="Paseo por la Vereda de la Estrella",
            difficulty=Activity.Difficulty.EASY,
            date=timezone.now() + timedelta(days=3),
        )
        self.future_hard = create_activity(
            organizer,
            title="Integral de Sierra Nevada",
            difficulty=Activity.Difficulty.HARD,
            date=timezone.now() + timedelta(days=30),
        )
        self.past = create_activity(
            organizer,
            title="Ruta ya celebrada",
            date=timezone.now() - timedelta(days=3),
        )

    def get_titles(self, params=""):
        response = self.client.get(f"/?{params}")
        return [a.title for a in response.context["activities"]]

    def test_default_shows_only_future_activities(self):
        titles = self.get_titles()
        self.assertIn(self.future_easy.title, titles)
        self.assertNotIn(self.past.title, titles)

    def test_filter_by_text(self):
        titles = self.get_titles("q=vereda")
        self.assertEqual(titles, [self.future_easy.title])

    def test_filter_by_difficulty(self):
        titles = self.get_titles("difficulty=hard")
        self.assertEqual(titles, [self.future_hard.title])

    def test_filter_by_date_range(self):
        date_to = (timezone.now() + timedelta(days=10)).date().isoformat()
        titles = self.get_titles(f"date_to={date_to}")
        self.assertEqual(titles, [self.future_easy.title])

    def test_include_past_activities(self):
        titles = self.get_titles("include_past=on")
        self.assertIn(self.past.title, titles)


GPX_CONTENT = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="37.0530" lon="-3.3110"><ele>2500</ele></trkpt>
    <trkpt lat="37.0540" lon="-3.3100"><ele>2550</ele></trkpt>
  </trkseg></trk>
</gpx>"""


class GpxUploadTests(TestCase):
    """Validación del archivo GPX (RF-07)."""

    def form_data(self):
        return {
            "title": "Ruta con track",
            "description": "Con GPX",
            "date": (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"),
            "difficulty": Activity.Difficulty.EASY,
            "location": "Sierra de Huétor",
            "meeting_point": "Área recreativa",
            "max_participants": 5,
        }

    def test_valid_gpx_file_is_accepted(self):
        gpx = SimpleUploadedFile("ruta.gpx", GPX_CONTENT)
        form = ActivityForm(self.form_data(), {"gpx_file": gpx})
        self.assertTrue(form.is_valid(), form.errors)

    def test_wrong_extension_is_rejected(self):
        wrong = SimpleUploadedFile("ruta.txt", b"no soy un gpx")
        form = ActivityForm(self.form_data(), {"gpx_file": wrong})
        self.assertFalse(form.is_valid())
        self.assertIn("gpx_file", form.errors)

    def test_oversized_file_is_rejected(self):
        big = SimpleUploadedFile("ruta.gpx", b"x" * (5 * 1024 * 1024 + 1))
        form = ActivityForm(self.form_data(), {"gpx_file": big})
        self.assertFalse(form.is_valid())
        self.assertIn("gpx_file", form.errors)
