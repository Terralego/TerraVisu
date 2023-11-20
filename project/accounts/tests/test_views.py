from django.test import TestCase, override_settings
from django.urls import reverse
from requests import HTTPError
from rest_framework.test import APITestCase

from project.accounts.models import PermanentAccessToken
from project.accounts.tests.factories import UserFactory


class LoginDispatchViewTestCase(TestCase):
    @override_settings(OIDC_ENABLE_LOGIN=True, OIDC_DISABLE_INTERNAL_LOGIN=False)
    def test_oidc_login_button_is_present(self):
        response = self.client.get(reverse("login_dispatcher"), follow=True)
        self.assertIn("OIDC", response.content.decode())

    @override_settings(OIDC_ENABLE_LOGIN=False)
    def test_oidc_login_button_is_not_present(self):
        response = self.client.get(reverse("login_dispatcher"), follow=True)
        self.assertNotIn("OIDC", response.content.decode())

    @override_settings(
        OIDC_ENABLE_LOGIN=True,
        OIDC_DISABLE_INTERNAL_LOGIN=True,
        AUTH_SERVER="http://example.com",
    )
    def test_login_redirection_if_internal_login_disabled(self):
        with self.assertRaises(HTTPError):
            # redirection works, but server doesn't exist
            self.client.get(reverse("login_dispatcher"), follow=True)


class FunctionalPermissionAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_list_anonymous(self):
        response = self.client.get(reverse("permission-list"))
        self.assertEqual(response.status_code, 401)

    def test_list_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("permission-list"))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_available_anonymous(self):
        response = self.client.get(reverse("permission-available"))
        self.assertEqual(response.status_code, 401)

    def test_available_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("permission-available"))
        self.assertEqual(response.status_code, 200)
        self.client.logout()


class LoginWithToken(TestCase):
    def test_wrong_token_raise_404(self):
        response = self.client.get(reverse("login_with_token") + "?token=xxx")
        self.assertEqual(response.status_code, 404)

    def test_correct_token_session_auth_and_redirect(self):
        user = UserFactory()
        access_token = PermanentAccessToken.objects.create(user=user)
        response = self.client.get(
            reverse("login_with_token") + f"?token={access_token.token}&url=/"
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
