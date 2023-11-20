from django.test import TestCase

from project.accounts.models import FunctionalPermission, PermanentAccessToken
from project.accounts.tests.factories import SuperUserFactory, UserFactory


class UserModelTestCase(TestCase):
    def test_superuser_has_all_permissions(self):
        user = SuperUserFactory()
        self.assertEqual(
            FunctionalPermission.objects.count(), user.functional_permissions.count()
        )

    def test_inactive_user_has_no_permissions(self):
        user = UserFactory(is_active=False)
        self.assertEqual(0, user.functional_permissions.count())

    def test_get_jwt_token(self):
        user = SuperUserFactory()
        self.assertIsNotNone(user.get_jwt_token())


class PermanentAccesstokenTestCase(TestCase):
    def test_str(self):
        user = UserFactory()
        access_token = PermanentAccessToken.objects.create(user=user)
        self.assertEqual(str(access_token), f"{user} - {access_token.token}")
