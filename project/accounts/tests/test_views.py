from django.test import TestCase
from django.urls import reverse

from project.accounts import settings


class LoginDispatchViewTestCase(TestCase):
    def test_oidc_login_button_is_present(self):
        initial_enable_login = settings.OIDC_ENABLE_LOGIN
        initial_disable_internal = settings.OIDC_DISABLE_INTERNAL_LOGIN
        settings.OIDC_DISABLE_INTERNAL_LOGIN = False
        settings.OIDC_ENABLE_LOGIN = True
        response = self.client.get(reverse("login_dispatcher"), follow=True)
        self.assertIn("OIDC", response.content.decode())
        settings.OIDC_ENABLE_LOGIN = initial_enable_login
        settings.OIDC_DISABLE_INTERNAL_LOGIN = initial_disable_internal

    def test_oidc_login_button_is_not_present(self):
        initial_enable_login = settings.OIDC_ENABLE_LOGIN
        settings.OIDC_ENABLE_LOGIN = False
        response = self.client.get(reverse("login_dispatcher"), follow=True)
        self.assertNotIn("OIDC", response.content.decode())
        settings.OIDC_ENABLE_LOGIN = initial_enable_login

    def test_login_redirection_if_internal_login_disabled(self):
        initial_enable_login = settings.OIDC_ENABLE_LOGIN
        initial_disable_internal = settings.OIDC_DISABLE_INTERNAL_LOGIN
        settings.OIDC_ENABLE_LOGIN = True
        settings.OIDC_DISABLE_INTERNAL_LOGIN = True
        response = self.client.get(reverse("login_dispatcher"), follow=True)
        self.assertEqual(
            response.status_code, 400
        )  # as no OIDC is configured, it will fail
        settings.OIDC_ENABLE_LOGIN = initial_enable_login
        settings.OIDC_DISABLE_INTERNAL_LOGIN = initial_disable_internal
