from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from listings.models import Category, Service

from .models import Conversation, Favorite, Order, Payment

User = get_user_model()


class MarketplaceFlowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer", password="pass12345")
        self.provider = User.objects.create_user(username="provider", password="pass12345")
        category = Category.objects.create(name="Test", slug="test", icon="⚡")
        self.service = Service.objects.create(
            provider=self.provider,
            category=category,
            title="Test service",
            description="Description",
            price=2500,
            city="Москва",
        )
        self.client.login(username="customer", password="pass12345")

    def test_favorite_toggle(self):
        self.client.post(reverse("marketplace:favorite_toggle", args=[self.service.id]))
        self.assertTrue(Favorite.objects.filter(user=self.customer, service=self.service).exists())
        self.client.post(reverse("marketplace:favorite_toggle", args=[self.service.id]))
        self.assertFalse(Favorite.objects.filter(user=self.customer, service=self.service).exists())

    def test_order_create(self):
        response = self.client.post(
            reverse("marketplace:order_create", args=[self.service.id]),
            {"note": "К субботе"},
        )
        order = Order.objects.get()
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.provider, self.provider)
        self.assertEqual(order.price, self.service.price)
        self.assertTrue(Payment.objects.filter(order=order, status=Payment.Status.PENDING).exists())
        self.assertRedirects(response, reverse("marketplace:payment_checkout", args=[order.id]))

    def test_conversation_and_message(self):
        response = self.client.post(reverse("marketplace:conversation_start", args=[self.service.id]))
        conversation = Conversation.objects.get()
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            reverse("marketplace:conversation", args=[conversation.id]),
            {"text": "Здравствуйте!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(conversation.messages.count(), 1)

    def test_provider_can_accept_order(self):
        order = Order.objects.create(
            customer=self.customer,
            provider=self.provider,
            service=self.service,
            price=self.service.price,
        )
        self.client.logout()
        self.client.login(username="provider", password="pass12345")
        self.client.post(reverse("marketplace:order_status", args=[order.id, "accepted"]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.ACCEPTED)

    def test_favorite_toggle_ajax(self):
        response = self.client.post(
            reverse("marketplace:favorite_toggle", args=[self.service.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorite"])

    def test_order_can_store_requested_schedule(self):
        self.client.post(
            reverse("marketplace:order_create", args=[self.service.id]),
            {"desired_date": "2026-10-10", "desired_time": "18:30", "note": "После работы"},
        )
        order = Order.objects.get()
        self.assertEqual(str(order.desired_date), "2026-10-10")
        self.assertEqual(order.desired_time.strftime("%H:%M"), "18:30")


class FinalProductFlowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="final_customer", password="pass12345")
        self.provider = User.objects.create_user(username="final_provider", password="pass12345")
        category = Category.objects.create(name="Final Test", slug="final-test", icon="F")
        self.service = Service.objects.create(
            provider=self.provider, category=category, title="Final service",
            description="Final flow", price=3200, city="Казань",
        )

    def test_customer_cannot_order_own_service(self):
        self.client.login(username="final_provider", password="pass12345")
        response = self.client.post(reverse("marketplace:order_create", args=[self.service.id]), {"note": "self"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.exists())

    def test_full_order_status_chain(self):
        order = Order.objects.create(
            customer=self.customer, provider=self.provider, service=self.service,
            price=self.service.price, status=Order.Status.NEW,
        )
        self.client.login(username="final_provider", password="pass12345")
        for status in [Order.Status.ACCEPTED, Order.Status.IN_PROGRESS, Order.Status.COMPLETED]:
            response = self.client.post(reverse("marketplace:order_status", args=[order.id, status]))
            self.assertEqual(response.status_code, 302)
            order.refresh_from_db()
            self.assertEqual(order.status, status)

    def test_provider_cannot_skip_statuses(self):
        order = Order.objects.create(
            customer=self.customer, provider=self.provider, service=self.service,
            price=self.service.price, status=Order.Status.NEW,
        )
        self.client.login(username="final_provider", password="pass12345")
        self.client.post(reverse("marketplace:order_status", args=[order.id, Order.Status.COMPLETED]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.NEW)


class PaymentSimulationTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="pay_customer", password="pass12345")
        self.provider = User.objects.create_user(username="pay_provider", password="pass12345")
        category = Category.objects.create(name="Payment Test", slug="payment-test", icon="P")
        self.service = Service.objects.create(provider=self.provider, category=category, title="Payment service", description="Payment", price=4900, city="Москва")
        self.order = Order.objects.create(customer=self.customer, provider=self.provider, service=self.service, price=self.service.price)
        self.payment = Payment.objects.create(order=self.order, amount=self.order.price)
        self.client.login(username="pay_customer", password="pass12345")

    def test_successful_demo_card_payment(self):
        response = self.client.post(reverse("marketplace:payment_checkout", args=[self.order.id]), {
            "method": "card", "card_holder": "IVAN IVANOV", "card_number": "4242 4242 4242 4242", "expiry": "12/30", "cvv": "123"
        })
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.payment.card_last4, "4242")
        self.assertTrue(self.payment.transaction_id.startswith("DUIT-"))
        self.assertRedirects(response, reverse("marketplace:payment_success", args=[self.order.id]))

    def test_declined_demo_card(self):
        self.client.post(reverse("marketplace:payment_checkout", args=[self.order.id]), {
            "method": "card", "card_holder": "IVAN IVANOV", "card_number": "4000 0000 0000 0002", "expiry": "12/30", "cvv": "123"
        })
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.FAILED)
        self.assertEqual(self.payment.card_last4, "0002")

    def test_after_service_payment(self):
        response = self.client.post(reverse("marketplace:payment_checkout", args=[self.order.id]), {"method": "after_service"})
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.method, Payment.Method.AFTER_SERVICE)
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        self.assertRedirects(response, reverse("marketplace:order_detail", args=[self.order.id]))

    def test_provider_cannot_pay_customer_order(self):
        self.client.logout(); self.client.login(username="pay_provider", password="pass12345")
        response = self.client.get(reverse("marketplace:payment_checkout", args=[self.order.id]))
        self.assertRedirects(response, reverse("marketplace:order_detail", args=[self.order.id]))

    def test_paid_order_is_refunded_on_cancel(self):
        self.payment.status = Payment.Status.PAID
        self.payment.method = Payment.Method.CARD
        self.payment.card_last4 = "4242"
        self.payment.save()
        self.client.post(reverse("marketplace:order_status", args=[self.order.id, Order.Status.CANCELLED]))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)

class FinalReleaseSafetyTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="safe_customer", password="pass12345")
        self.provider = User.objects.create_user(username="safe_provider", password="pass12345")
        self.provider.profile.role = "provider"
        self.provider.profile.save(update_fields=["role"])
        category = Category.objects.create(name="Safety Test", slug="safety-test", icon="S")
        self.service = Service.objects.create(
            provider=self.provider, category=category, title="Safety service",
            description="Safety", price=2500, city="Москва",
        )

    def test_provider_who_buys_becomes_both(self):
        other_provider = User.objects.create_user(username="other_provider", password="pass12345")
        other_service = Service.objects.create(
            provider=other_provider, category=self.service.category, title="Other service",
            description="Other", price=1800, city="Москва",
        )
        self.client.login(username="safe_provider", password="pass12345")
        self.client.post(reverse("marketplace:order_create", args=[other_service.id]), {"note": "Хочу заказать"})
        self.provider.profile.refresh_from_db()
        self.assertEqual(self.provider.profile.role, "both")

    def test_cancelled_order_cannot_be_paid(self):
        order = Order.objects.create(
            customer=self.customer, provider=self.provider, service=self.service,
            price=self.service.price, status=Order.Status.CANCELLED,
        )
        Payment.objects.create(order=order, amount=order.price)
        self.client.login(username="safe_customer", password="pass12345")
        response = self.client.get(reverse("marketplace:payment_checkout", args=[order.id]))
        self.assertRedirects(response, reverse("marketplace:order_detail", args=[order.id]))

    def test_refunded_payment_cannot_be_paid_again(self):
        order = Order.objects.create(
            customer=self.customer, provider=self.provider, service=self.service,
            price=self.service.price, status=Order.Status.CANCELLED,
        )
        Payment.objects.create(order=order, amount=order.price, status=Payment.Status.REFUNDED)
        self.client.login(username="safe_customer", password="pass12345")
        response = self.client.get(reverse("marketplace:payment_checkout", args=[order.id]))
        self.assertRedirects(response, reverse("marketplace:order_detail", args=[order.id]))
