from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ActivityForm
from .models import (
    Activity,
    ActivityPhoto,
    Registration,
    register_user_for_activity,
)

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

    def test_max_participants_cannot_drop_below_registered(self):
        """Al editar, el aforo no puede quedar por debajo de los inscritos."""
        register_user_for_activity(create_user("ana"), self.activity.pk)
        register_user_for_activity(create_user("luis"), self.activity.pk)
        self.client.force_login(self.organizer)
        response = self.client.post(
            reverse("activity_edit", args=[self.activity.pk]),
            {
                "title": self.activity.title,
                "description": self.activity.description,
                "date": (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"),
                "difficulty": self.activity.difficulty,
                "location": self.activity.location,
                "meeting_point": self.activity.meeting_point,
                "max_participants": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no puede ser menor")
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.max_participants, 2)

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

    def test_admin_can_delete_any_activity(self):
        admin = create_user("admin")
        admin.is_staff = True
        admin.save()
        self.client.force_login(admin)
        response = self.client.post(
            reverse("activity_delete", args=[self.activity.pk])
        )
        self.assertRedirects(response, reverse("activity_list"))
        self.assertFalse(Activity.objects.filter(pk=self.activity.pk).exists())

    def test_admin_cannot_edit_others_activity(self):
        admin = create_user("admin")
        admin.is_staff = True
        admin.save()
        self.client.force_login(admin)
        response = self.client.get(reverse("activity_edit", args=[self.activity.pk]))
        self.assertEqual(response.status_code, 403)


class ActivityChatTests(TestCase):
    """Chat de actividad: solo organizador e inscritos."""

    def setUp(self):
        self.organizer = create_user("organizadora")
        self.member = create_user("montanera")
        self.outsider = create_user("curiosa")
        self.activity = create_activity(self.organizer)
        register_user_for_activity(self.member, self.activity.pk)

    def send(self, text="¡Nos vemos en el parking!"):
        return self.client.post(
            reverse("chat_send", args=[self.activity.pk]), {"content": text}
        )

    def test_registered_user_can_send_and_read_messages(self):
        self.client.force_login(self.member)
        response = self.send()
        self.assertEqual(response.status_code, 201)
        response = self.client.get(reverse("chat_messages", args=[self.activity.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["content"], "¡Nos vemos en el parking!")
        self.assertTrue(data["messages"][0]["mine"])

    def test_organizer_can_use_chat(self):
        self.client.force_login(self.organizer)
        self.assertEqual(self.send().status_code, 201)

    def test_non_registered_user_cannot_use_chat(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.send().status_code, 403)
        response = self.client.get(reverse("chat_messages", args=[self.activity.pk]))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(reverse("chat_messages", args=[self.activity.pk]))
        self.assertEqual(response.status_code, 302)

    def test_empty_message_is_rejected(self):
        self.client.force_login(self.member)
        self.assertEqual(self.send("   ").status_code, 400)

    def test_user_who_cancels_loses_chat_access(self):
        self.client.force_login(self.member)
        self.client.post(reverse("registration_cancel", args=[self.activity.pk]))
        self.assertEqual(self.send().status_code, 403)


# PNG mínimo de 1x1 píxel, suficiente para que Pillow lo valide.
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x1e\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)


def tiny_image(name="foto.png"):
    return SimpleUploadedFile(name, TINY_PNG, content_type="image/png")


class ActivityPhotoTests(TestCase):
    """Fotos de la ruta: subida y borrado con permisos."""

    def setUp(self):
        self.organizer = create_user("organizadora")
        self.other = create_user("otra")
        self.activity = create_activity(self.organizer)

    def tearDown(self):
        for photo in ActivityPhoto.objects.all():
            photo.image.delete(save=False)

    def upload(self, files):
        return self.client.post(
            reverse("activity_photo_add", args=[self.activity.pk]),
            {"images": files},
        )

    def test_organizer_can_upload_multiple_photos(self):
        self.client.force_login(self.organizer)
        response = self.upload([tiny_image("a.png"), tiny_image("b.png")])
        self.assertRedirects(response, self.activity.get_absolute_url())
        self.assertEqual(self.activity.photos.count(), 2)

    def test_non_organizer_cannot_upload(self):
        self.client.force_login(self.other)
        response = self.upload([tiny_image()])
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.activity.photos.count(), 0)

    def test_non_image_file_is_skipped(self):
        self.client.force_login(self.organizer)
        fake = SimpleUploadedFile("nota.txt", b"no soy imagen", content_type="text/plain")
        self.upload([fake])
        self.assertEqual(self.activity.photos.count(), 0)

    def test_organizer_can_delete_photo(self):
        photo = ActivityPhoto.objects.create(
            activity=self.activity, image=tiny_image()
        )
        self.client.force_login(self.organizer)
        self.client.post(reverse("activity_photo_delete", args=[photo.pk]))
        self.assertEqual(self.activity.photos.count(), 0)

    def test_other_user_cannot_delete_photo(self):
        photo = ActivityPhoto.objects.create(
            activity=self.activity, image=tiny_image()
        )
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("activity_photo_delete", args=[photo.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.activity.photos.count(), 1)


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
        response = self.client.get(f"{reverse('activity_list')}?{params}")
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

    def test_gpx_is_saved_when_creating_through_the_view(self):
        """Regresión: la vista debe pasar request.FILES al formulario."""
        user = create_user("organizadora")
        self.client.force_login(user)
        data = self.form_data()
        data["gpx_file"] = SimpleUploadedFile("ruta.gpx", GPX_CONTENT)
        response = self.client.post(reverse("activity_create"), data)
        activity = Activity.objects.get(title=data["title"])
        self.assertRedirects(response, activity.get_absolute_url())
        self.assertTrue(activity.gpx_file, "El GPX no se guardó al crear la actividad")
        activity.gpx_file.delete(save=False)

    def test_gpx_upload_sets_coordinates_for_weather(self):
        """El primer punto del track alimenta el parte meteorológico."""
        user = create_user("organizadora")
        self.client.force_login(user)
        data = self.form_data()
        data["gpx_file"] = SimpleUploadedFile("ruta.gpx", GPX_CONTENT)
        self.client.post(reverse("activity_create"), data)
        activity = Activity.objects.get(title=data["title"])
        self.assertAlmostEqual(activity.latitude, 37.0530, places=4)
        self.assertAlmostEqual(activity.longitude, -3.3110, places=4)
        activity.gpx_file.delete(save=False)

    def test_gpx_is_saved_when_editing_through_the_view(self):
        user = create_user("organizadora")
        activity = create_activity(user)
        self.client.force_login(user)
        data = self.form_data()
        data["gpx_file"] = SimpleUploadedFile("ruta.gpx", GPX_CONTENT)
        self.client.post(reverse("activity_edit", args=[activity.pk]), data)
        activity.refresh_from_db()
        self.assertTrue(activity.gpx_file, "El GPX no se guardó al editar la actividad")
        activity.gpx_file.delete(save=False)
