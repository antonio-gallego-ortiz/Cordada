from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .validators import validate_upload_size


class FakeFile:
    def __init__(self, size):
        self.size = size


class UploadSizeValidatorTests(TestCase):
    """Límite de tamaño común a todas las subidas de usuarios."""

    def test_small_file_is_accepted(self):
        validate_upload_size(FakeFile(5 * 1024 * 1024))

    def test_oversized_file_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload_size(FakeFile(5 * 1024 * 1024 + 1))


class PlatformTests(TestCase):
    """Piezas transversales de la plataforma."""

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "User-agent")

    def test_legal_pages(self):
        for url_name in ("privacy", "terms"):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)

    def test_custom_404_page(self):
        response = self.client.get("/no-existe/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response, "Te has salido del sendero", status_code=404
        )
