from django.test import TestCase
from django.urls import reverse


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
