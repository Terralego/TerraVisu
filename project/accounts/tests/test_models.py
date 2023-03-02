from django.test import TestCase

from project.accounts.models import FunctionalPermission
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
