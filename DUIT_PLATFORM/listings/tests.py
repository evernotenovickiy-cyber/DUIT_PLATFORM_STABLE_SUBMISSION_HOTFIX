import io
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Category, Service, ServicePhoto
from marketplace.models import Order
from reviews.models import Review


def image_file(name, color):
    buf = io.BytesIO()
    Image.new("RGB", (80, 80), color).save(buf, format="JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


class ServiceUploadTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="maker", password="StrongPass928!")
        self.category = Category.objects.create(name="Кондитеры")
        self.client.login(username="maker", password="StrongPass928!")

    def test_create_service_with_multiple_photos(self):
        response = self.client.post(
            reverse("listings:service_create"),
            {
                "title": "Тестовая услуга",
                "category": self.category.pk,
                "description": "Описание услуги",
                "price": "1500",
                "city": "Москва",
                "is_active": "on",
                "photos": [image_file("one.jpg", "red"), image_file("two.jpg", "blue")],
            },
        )
        self.assertEqual(response.status_code, 302)
        service = Service.objects.get(title="Тестовая услуга")
        self.assertEqual(ServicePhoto.objects.filter(service=service).count(), 2)


    def test_non_image_upload_is_rejected(self):
        bad = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")
        response = self.client.post(
            reverse("listings:service_create"),
            {
                "title": "Bad upload",
                "category": self.category.pk,
                "description": "Описание",
                "price": "1000",
                "city": "Москва",
                "is_active": "on",
                "photos": [bad],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Service.objects.filter(title="Bad upload").exists())


class UnicodeSlugRoutingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="unicode_maker", password="StrongPass928!"
        )
        self.category = Category.objects.create(name="Ремонт и стройка")
        self.service = Service.objects.create(
            provider=self.user,
            category=self.category,
            title="Мелкий бытовой ремонт муж на час",
            description="Тест маршрута с кириллическим slug.",
            price=1500,
            city="Казань",
        )

    def test_unicode_slug_reverses_and_detail_opens(self):
        self.assertTrue(any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in self.service.slug))
        url = reverse("listings:service_detail", kwargs={"slug": self.service.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.title)

    def test_home_renders_with_unicode_slug_service(self):
        response = self.client.get(reverse("listings:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.title)

class ExpandedCatalogTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog_maker", password="StrongPass928!"
        )
        self.nails = Category.objects.create(name="Маникюр и педикюр", icon="💅")
        self.grooming = Category.objects.create(name="Груминг", icon="🐕")
        Service.objects.create(
            provider=self.user,
            category=self.nails,
            title="Маникюр тест",
            description="Красота",
            price=2000,
            city="Москва",
        )
        Service.objects.create(
            provider=self.user,
            category=self.grooming,
            title="Груминг тест",
            description="Питомцы",
            price=2500,
            city="Москва",
        )

    def test_group_filter_separates_service_spheres(self):
        response = self.client.get(reverse("listings:catalog"), {"group": "pets"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Груминг тест")
        self.assertNotContains(response, "Маникюр тест")

    def test_catalog_price_filter(self):
        response = self.client.get(
            reverse("listings:catalog"), {"min_price": "2300", "max_price": "3000"}
        )
        self.assertContains(response, "Груминг тест")
        self.assertNotContains(response, "Маникюр тест")

class ProductPolishTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="polish_maker", password="StrongPass928!")
        self.cat = Category.objects.create(name="Сантехника", icon="🚿")
        self.service = Service.objects.create(
            provider=self.user, category=self.cat, title="Замена смесителя",
            description="Починю кран и сантехнику", price=2200, city="Москва",
            service_format="visit", pricing_type="fixed", completed_orders=27,
        )

    def test_synonym_search_finds_service(self):
        response = self.client.get(reverse("listings:catalog"), {"q": "кран"})
        self.assertContains(response, "Замена смесителя")

    def test_format_filter(self):
        response = self.client.get(reverse("listings:catalog"), {"format": "visit"})
        self.assertContains(response, "Замена смесителя")
        response = self.client.get(reverse("listings:catalog"), {"format": "online"})
        self.assertNotContains(response, "Замена смесителя")


class VerifiedReviewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(username="review_customer", password="pass12345")
        self.provider = User.objects.create_user(username="review_provider", password="pass12345")
        self.category = Category.objects.create(name="Review Category", slug="review-category", icon="R")
        self.service = Service.objects.create(
            provider=self.provider, category=self.category, title="Review service",
            description="Description", price=1800, city="Москва"
        )
        self.client.login(username="review_customer", password="pass12345")

    def test_review_requires_completed_order(self):
        response = self.client.post(self.service.get_absolute_url(), {"rating": "5", "text": "Отлично"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.filter(service=self.service, author=self.customer).exists())

    def test_review_allowed_after_completed_order(self):
        Order.objects.create(
            customer=self.customer, provider=self.provider, service=self.service,
            price=self.service.price, status=Order.Status.COMPLETED
        )
        response = self.client.post(self.service.get_absolute_url(), {"rating": "5", "text": "Отлично"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(service=self.service, author=self.customer).exists())

class FinalPageSmokeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.provider = User.objects.create_user(username="smoke_provider", password="StrongPass928!", first_name="Анна", last_name="Смирнова")
        self.provider.profile.role = "provider"
        self.provider.profile.city = "Москва"
        self.provider.profile.headline = "Мастер тестовой услуги"
        self.provider.profile.save()
        self.customer = User.objects.create_user(username="smoke_customer", password="StrongPass928!", first_name="Иван")
        self.customer.profile.role = "customer"
        self.customer.profile.save(update_fields=["role"])
        self.category = Category.objects.create(name="Маникюр и педикюр", icon="💅")
        self.service = Service.objects.create(
            provider=self.provider, category=self.category, title="Маникюр для smoke test",
            description="Полное описание тестовой услуги", price=2500, city="Москва",
            demo_image_url="https://example.com/image.jpg", service_format="provider",
        )

    def test_public_product_pages_render(self):
        urls = [
            reverse("listings:home"), reverse("listings:catalog"), self.service.get_absolute_url(),
            reverse("listings:provider_detail", args=[self.provider.username]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_customer_dashboard_renders(self):
        self.client.login(username="smoke_customer", password="StrongPass928!")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "РЕЖИМ ЗАКАЗЧИКА")

    def test_provider_dashboard_and_publish_form_render(self):
        self.client.login(username="smoke_provider", password="StrongPass928!")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "РЕЖИМ ИСПОЛНИТЕЛЯ")
        response = self.client.get(reverse("listings:service_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Создайте витрину услуги")

    def test_service_detail_contains_back_navigation(self):
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, "Назад к каталогу")

class ServiceDeleteSafetyTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.provider = User.objects.create_user(username="delete_provider", password="pass12345")
        self.customer = User.objects.create_user(username="delete_customer", password="pass12345")
        self.category = Category.objects.create(name="Delete Safety", slug="delete-safety", icon="D")
        self.service = Service.objects.create(
            provider=self.provider, category=self.category, title="Service with order",
            description="Must be archived", price=1000, city="Москва",
        )
        Order.objects.create(
            customer=self.customer, provider=self.provider, service=self.service,
            price=self.service.price,
        )
        self.client.login(username="delete_provider", password="pass12345")

    def test_service_with_order_is_archived_instead_of_500(self):
        response = self.client.post(reverse("listings:service_delete", args=[self.service.slug]))
        self.assertEqual(response.status_code, 302)
        self.service.refresh_from_db()
        self.assertFalse(self.service.is_active)

from django.test import SimpleTestCase
from listings.management.commands.seed_demo import avatar_url, service_photo, CATEGORY_PHOTO_IDS
from listings.catalog_data import CATEGORY_GROUPS, RUSSIA_CITIES


class DemoMediaPolicyTests(SimpleTestCase):
    def test_avatar_urls_are_gendered_and_unique(self):
        female = [avatar_url("f", i) for i in range(100)]
        male = [avatar_url("m", i) for i in range(100)]
        self.assertEqual(len(set(female)), 100)
        self.assertEqual(len(set(male)), 100)
        self.assertTrue(all("/portraits/women/" in url for url in female))
        self.assertTrue(all("/portraits/men/" in url for url in male))
        self.assertFalse(set(female) & set(male))

    def test_all_catalog_categories_have_fixed_curated_pools(self):
        categories = [name for group in CATEGORY_GROUPS for name, _ in group["items"]]
        self.assertEqual(set(categories), set(CATEGORY_PHOTO_IDS))
        self.assertTrue(all(len(CATEGORY_PHOTO_IDS[name]) >= len(RUSSIA_CITIES) for name in categories))

    def test_photo_ids_do_not_overlap_between_categories(self):
        seen = set()
        for ids in CATEGORY_PHOTO_IDS.values():
            self.assertFalse(seen.intersection(ids))
            seen.update(ids)

    def test_same_category_each_city_uses_different_photo(self):
        urls = {
            service_photo("Барберы", "beauty", city_index=i, category_index=0, unique_key=i)
            for i in range(len(RUSSIA_CITIES))
        }
        self.assertEqual(len(urls), len(RUSSIA_CITIES))
        self.assertTrue(all(url.startswith("/static/demo/services/") for url in urls))
        self.assertTrue(all(url.endswith(".jpg") for url in urls))

    def test_plumbing_uses_only_curated_plumbing_ids(self):
        for city_index in range(len(RUSSIA_CITIES)):
            url = service_photo("Сантехника", "home", city_index=city_index, unique_key=city_index)
            photo_id = int(url.rsplit("/", 1)[1].split(".", 1)[0])
            self.assertIn(photo_id, CATEGORY_PHOTO_IDS["Сантехника"])

    def test_courier_and_auto_photo_ids_are_disjoint(self):
        self.assertTrue(set(CATEGORY_PHOTO_IDS["Курьеры"]).isdisjoint(CATEGORY_PHOTO_IDS["Ремонт автомобилей"]))
