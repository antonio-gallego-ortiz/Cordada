from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ListingForm
from .models import Conversation, Listing, ListingImage, MarketMessage

User = get_user_model()


def create_user(username, **extra):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="montana-segura-99",
        **extra,
    )


def create_listing(seller, **kwargs):
    defaults = {
        "title": "Botas Sportiva Trango",
        "description": "Talla 42, dos temporadas de uso.",
        "category": Listing.Category.FOOTWEAR,
        "condition": Listing.Condition.GOOD,
        "offer_type": Listing.OfferType.SALE,
        "price": "80.00",
        "location": "Granada",
        "seller": seller,
    }
    defaults.update(kwargs)
    return Listing.objects.create(**defaults)


class ListingPermissionTests(TestCase):
    """Permisos del CRUD de anuncios."""

    def setUp(self):
        self.seller = create_user("vendedora")
        self.other = create_user("otra")
        self.listing = create_listing(self.seller)

    def test_anonymous_user_cannot_publish(self):
        response = self.client.get(reverse("listing_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_only_seller_can_edit(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("listing_edit", args=[self.listing.pk]))
        self.assertEqual(response.status_code, 403)

    def test_only_seller_can_change_status(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("listing_set_status", args=[self.listing.pk]),
            {"status": "closed"},
        )
        self.assertEqual(response.status_code, 403)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.AVAILABLE)

    def test_seller_can_mark_as_reserved(self):
        self.client.force_login(self.seller)
        self.client.post(
            reverse("listing_set_status", args=[self.listing.pk]),
            {"status": "reserved"},
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.RESERVED)

    def test_other_user_cannot_delete(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("listing_delete", args=[self.listing.pk]))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete_any_listing(self):
        admin = create_user("admin", is_staff=True)
        self.client.force_login(admin)
        response = self.client.post(reverse("listing_delete", args=[self.listing.pk]))
        self.assertRedirects(response, reverse("listing_list"))
        self.assertFalse(Listing.objects.filter(pk=self.listing.pk).exists())


class ListingFormTests(TestCase):
    """Validación del formulario de anuncios."""

    def form_data(self, **overrides):
        data = {
            "title": "Cuerda 60 m",
            "description": "Cuerda dinámica en buen estado.",
            "category": Listing.Category.CLIMBING,
            "condition": Listing.Condition.GOOD,
            "offer_type": Listing.OfferType.SALE,
            "price": "60.00",
            "location": "Madrid",
        }
        data.update(overrides)
        return data

    def test_sale_requires_price(self):
        form = ListingForm(self.form_data(price=""))
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_loan_clears_price(self):
        form = ListingForm(
            self.form_data(offer_type=Listing.OfferType.LOAN, price="10.00")
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["price"])


class ConversationTests(TestCase):
    """Chat privado comprador-vendedor."""

    def setUp(self):
        self.seller = create_user("vendedora")
        self.buyer = create_user("compradora")
        self.outsider = create_user("fisgona")
        self.listing = create_listing(self.seller)

    def start_conversation(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("conversation_start", args=[self.listing.pk]))
        return Conversation.objects.get(listing=self.listing, buyer=self.buyer)

    def test_buyer_can_start_conversation(self):
        conversation = self.start_conversation()
        self.assertEqual(conversation.listing.seller, self.seller)

    def test_starting_twice_reuses_conversation(self):
        self.start_conversation()
        self.client.post(reverse("conversation_start", args=[self.listing.pk]))
        self.assertEqual(Conversation.objects.count(), 1)

    def test_seller_cannot_chat_with_self(self):
        self.client.force_login(self.seller)
        self.client.post(reverse("conversation_start", args=[self.listing.pk]))
        self.assertEqual(Conversation.objects.count(), 0)

    def test_participants_can_send_and_read(self):
        conversation = self.start_conversation()
        response = self.client.post(
            reverse("conversation_send", args=[conversation.pk]),
            {"content": "¿Sigue disponible?"},
        )
        self.assertEqual(response.status_code, 201)

        self.client.force_login(self.seller)
        response = self.client.get(
            reverse("conversation_messages", args=[conversation.pk])
        )
        data = response.json()
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["content"], "¿Sigue disponible?")
        self.assertFalse(data["messages"][0]["mine"])

    def test_outsider_cannot_access_conversation(self):
        conversation = self.start_conversation()
        MarketMessage.objects.create(
            conversation=conversation, sender=self.buyer, content="Hola"
        )
        self.client.force_login(self.outsider)
        for url_name in ("conversation_detail", "conversation_messages"):
            response = self.client.get(reverse(url_name, args=[conversation.pk]))
            self.assertEqual(response.status_code, 403)
        response = self.client.post(
            reverse("conversation_send", args=[conversation.pk]), {"content": "Hola"}
        )
        self.assertEqual(response.status_code, 403)


class ListingImageTests(TestCase):
    """Imágenes múltiples en los anuncios."""

    TINY_PNG = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x00\x03\x00\x01\x1e\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def tiny_image(self, name):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(name, self.TINY_PNG, content_type="image/png")

    def setUp(self):
        self.seller = create_user("vendedora")
        self.other = create_user("otra")

    def tearDown(self):
        for listing_image in ListingImage.objects.all():
            listing_image.image.delete(save=False)

    def test_listing_created_with_multiple_images(self):
        self.client.force_login(self.seller)
        response = self.client.post(
            reverse("listing_create"),
            {
                "title": "Piolet clásico",
                "description": "Bien cuidado.",
                "category": Listing.Category.CLIMBING,
                "condition": Listing.Condition.GOOD,
                "offer_type": Listing.OfferType.SALE,
                "price": "40.00",
                "location": "Granada",
                "images": [self.tiny_image("a.png"), self.tiny_image("b.png")],
            },
        )
        listing = Listing.objects.get(title="Piolet clásico")
        self.assertRedirects(response, listing.get_absolute_url())
        self.assertEqual(listing.images.count(), 2)
        self.assertIsNotNone(listing.main_photo)

    def test_only_seller_or_admin_can_delete_image(self):
        listing = create_listing(self.seller)
        listing_image = ListingImage(listing=listing)
        listing_image.image.save("foto.png", self.tiny_image("foto.png"), save=True)

        self.client.force_login(self.other)
        response = self.client.post(
            reverse("listing_image_delete", args=[listing_image.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(listing.images.count(), 1)

        self.client.force_login(self.seller)
        self.client.post(reverse("listing_image_delete", args=[listing_image.pk]))
        self.assertEqual(listing.images.count(), 0)


class ListingSearchTests(TestCase):
    """Búsqueda y filtrado del mercado."""

    def setUp(self):
        seller = create_user("vendedora")
        self.boots = create_listing(seller, title="Botas rígidas", price="80.00")
        self.skis = create_listing(
            seller,
            title="Esquís de travesía",
            category=Listing.Category.SNOW,
            offer_type=Listing.OfferType.RENT,
            price="15.00",
        )
        self.sold = create_listing(
            seller, title="Piolet vendido", status=Listing.Status.CLOSED
        )

    def get_titles(self, params=""):
        response = self.client.get(f"{reverse('listing_list')}?{params}")
        return [listing.title for listing in response.context["listings"]]

    def test_only_available_listings_are_shown(self):
        titles = self.get_titles()
        self.assertIn(self.boots.title, titles)
        self.assertNotIn(self.sold.title, titles)

    def test_filter_by_text(self):
        self.assertEqual(self.get_titles("q=esquís"), [self.skis.title])

    def test_filter_by_category(self):
        self.assertEqual(self.get_titles("category=snow"), [self.skis.title])

    def test_filter_by_offer_type(self):
        self.assertEqual(self.get_titles("offer_type=rent"), [self.skis.title])

    def test_filter_by_max_price(self):
        self.assertEqual(self.get_titles("max_price=20"), [self.skis.title])
