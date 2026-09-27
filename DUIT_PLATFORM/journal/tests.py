from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Post


class JournalTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="author", password="StrongPass928!")
        self.post = Post.objects.create(author=self.user, title="Полезный материал", excerpt="Коротко", body="Полный текст", city="Москва")

    def test_index_and_detail_are_public(self):
        self.assertEqual(self.client.get(reverse("journal:index")).status_code, 200)
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Полезный материал")

    def test_authenticated_user_can_publish(self):
        self.client.login(username="author", password="StrongPass928!")
        response = self.client.post(reverse("journal:create"), {
            "kind": "guide", "city": "Казань", "title": "Новый совет",
            "excerpt": "Короткое описание", "body": "Полезный текст", "image_url": "",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(title="Новый совет", author=self.user).exists())
