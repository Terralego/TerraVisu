from django.test import TestCase
from django.urls import reverse

from project.accounts.tests.factories import SuperUserFactory


class FunctionalPermissionAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = SuperUserFactory()

    def setUp(self) -> None:
        self.client.force_login(self.superuser)

    def test_list(self):
        response = self.client.get(
            reverse("admin:accounts_functionalpermission_changelist")
        )
        self.assertEqual(response.status_code, 200)
