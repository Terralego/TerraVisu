from django.test import TestCase, override_settings
from django.urls import reverse
from requests import HTTPError
from rest_framework.test import APITestCase

from project.accounts.models import FunctionalPermission, PermanentAccessToken
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


class GroupViewSetAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.regular_user = UserFactory()
        cls.user_manager = UserFactory()
        cls.user_manager.user_permissions.add(
            FunctionalPermission.objects.get(codename="can_manage_users")
        )
        cls.group_manager = UserFactory()
        cls.group_manager.user_permissions.add(
            FunctionalPermission.objects.get(codename="can_manage_groups")
        )

    def test_group_list_forbidden_without_permission(self):
        self.client.force_authenticate(self.regular_user)
        response = self.client.get(reverse("group-list"))
        self.assertEqual(response.status_code, 403)

    def test_group_read_only_for_user_manager(self):
        self.client.force_authenticate(self.user_manager)
        get_response = self.client.get(reverse("group-list"))
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(reverse("group-list"), {"name": "NewGroup"})
        self.assertEqual(post_response.status_code, 403)

    def test_group_create_allowed_for_group_manager(self):
        self.client.force_authenticate(self.group_manager)
        response = self.client.post(reverse("group-list"), {"name": "NewGroup"})
        self.assertEqual(response.status_code, 201)


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
