from django.test import TestCase, override_settings
from django.urls import reverse
from requests import HTTPError


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
