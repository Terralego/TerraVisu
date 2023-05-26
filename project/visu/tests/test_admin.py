from django.test import TestCase

from project.accounts.tests.factories import SuperUserFactory


class AdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_admin_access(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
