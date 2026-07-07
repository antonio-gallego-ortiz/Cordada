from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Community, CommunityMessage, Membership

User = get_user_model()


def create_user(username, **extra):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="montana-segura-99",
        **extra,
    )


class CommunityTests(TestCase):
    """Comunidades: creación, pertenencia y permisos."""

    def setUp(self):
        self.creator = create_user("creadora")
        self.member = create_user("miembra")
        self.outsider = create_user("externa")
        self.community = Community.objects.create(
            name="Escaladores de Madrid",
            description="Grupo para quedar a escalar por la sierra.",
            created_by=self.creator,
        )
        Membership.objects.create(community=self.community, user=self.creator)
        Membership.objects.create(community=self.community, user=self.member)

    def test_creating_community_joins_creator(self):
        self.client.force_login(self.member)
        self.client.post(
            reverse("community_create"),
            {"name": "Alpinistas de Chamonix", "description": "Hielo y mixto."},
        )
        community = Community.objects.get(name="Alpinistas de Chamonix")
        self.assertTrue(community.is_member(self.member))

    def test_user_can_join_and_leave(self):
        self.client.force_login(self.outsider)
        self.client.post(reverse("community_join", args=[self.community.pk]))
        self.assertTrue(self.community.is_member(self.outsider))
        self.client.post(reverse("community_leave", args=[self.community.pk]))
        self.assertFalse(self.community.is_member(self.outsider))

    def test_join_twice_does_not_duplicate(self):
        self.client.force_login(self.member)
        self.client.post(reverse("community_join", args=[self.community.pk]))
        self.assertEqual(
            Membership.objects.filter(
                community=self.community, user=self.member
            ).count(),
            1,
        )

    def test_only_creator_or_admin_can_delete(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("community_delete", args=[self.community.pk])
        )
        self.assertEqual(response.status_code, 403)

        admin = create_user("admin", is_staff=True)
        self.client.force_login(admin)
        self.client.post(reverse("community_delete", args=[self.community.pk]))
        self.assertFalse(Community.objects.filter(pk=self.community.pk).exists())


class CommunityChatTests(TestCase):
    """Chat de grupo: solo para miembros."""

    def setUp(self):
        self.creator = create_user("creadora")
        self.member = create_user("miembra")
        self.outsider = create_user("externa")
        self.community = Community.objects.create(
            name="Amigos del esquí de fondo",
            description="Salidas los domingos.",
            created_by=self.creator,
        )
        Membership.objects.create(community=self.community, user=self.creator)
        Membership.objects.create(community=self.community, user=self.member)

    def send(self, text="¿Alguien sube el sábado?"):
        return self.client.post(
            reverse("community_send", args=[self.community.pk]), {"content": text}
        )

    def test_member_can_send_and_read(self):
        self.client.force_login(self.member)
        self.assertEqual(self.send().status_code, 201)
        response = self.client.get(
            reverse("community_messages", args=[self.community.pk])
        )
        data = response.json()
        self.assertEqual(len(data["messages"]), 1)
        self.assertTrue(data["messages"][0]["mine"])

    def test_non_member_cannot_use_chat(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.send().status_code, 403)
        response = self.client.get(
            reverse("community_messages", args=[self.community.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_member_who_leaves_loses_chat_access(self):
        self.client.force_login(self.member)
        self.client.post(reverse("community_leave", args=[self.community.pk]))
        self.assertEqual(self.send().status_code, 403)

    def test_empty_message_is_rejected(self):
        self.client.force_login(self.member)
        self.assertEqual(self.send("   ").status_code, 400)
        self.assertEqual(CommunityMessage.objects.count(), 0)
