from django.test import TestCase

from project.accounts.models import FunctionalPermission, User


class UserModelTestCase(TestCase):
    def test_superuser_has_all_permissions(self):
        user = User.objects.create_user(
            email="test", password="test", is_superuser=True
        )
        self.assertEqual(
            FunctionalPermission.objects.count(), user.functional_permissions.count()
        )

    def test_inactive_user_has_no_permissions(self):
        user = User.objects.create_user(email="test2", password="test", is_active=False)
        self.assertEqual(0, user.functional_permissions.count())
