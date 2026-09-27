from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile

User = get_user_model()


class RegistrationTests(TestCase):
    def test_registration_hashes_password_logs_user_in_and_saves_role(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "Анна", "last_name": "Иванова", "username": "new_user",
            "email": "new@example.com", "city": "Москва", "role": Profile.Role.PROVIDER,
            "password1": "StrongPass928!", "password2": "StrongPass928!",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="new_user")
        self.assertTrue(user.check_password("StrongPass928!"))
        self.assertNotEqual(user.password, "StrongPass928!")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertEqual(user.profile.role, Profile.Role.PROVIDER)
        self.assertEqual(user.profile.city, "Москва")

    def test_login_accepts_email(self):
        User.objects.create_user(username="shortlogin", email="mail@example.com", password="StrongPass928!")
        response = self.client.post(reverse("accounts:login"), {
            "username": "mail@example.com", "password": "StrongPass928!"
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_provider_registration_link_prefills_provider_role(self):
        response = self.client.get(reverse("accounts:register"), {"role": "provider"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["role"], Profile.Role.PROVIDER)


class DashboardRoleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="roleuser", password="StrongPass928!")
        self.client.login(username="roleuser", password="StrongPass928!")

    def test_customer_dashboard_uses_customer_mode(self):
        self.user.profile.role = Profile.Role.CUSTOMER
        self.user.profile.save(update_fields=["role"])
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["mode"], "customer")

    def test_both_account_can_switch_modes(self):
        self.user.profile.role = Profile.Role.BOTH
        self.user.profile.save(update_fields=["role"])
        response = self.client.get(reverse("accounts:dashboard"), {"mode": "provider"})
        self.assertEqual(response.context["mode"], "provider")
        self.assertTrue(response.context["can_switch_mode"])
