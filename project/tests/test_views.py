from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from project.accounts.tests.factories import UserFactory
from project.terra_layer.tests.factories import ReportFileFactory


class PrivateFilesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.report_file = ReportFileFactory()

    def test_logged_user_can_access_file(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("serve_private_files", kwargs={"path": self.report_file.file.name})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unlogged_cannot_access_file(self):
        response = self.client.get(
            reverse("serve_private_files", kwargs={"path": self.report_file.file.name})
        )
        self.assertRedirects(
            response, f"/accounts/login/?next=/private/{self.report_file.file.name}"
        )

    def test_404_missing_file(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "serve_private_files", kwargs={"path": "report_file/idontexist.pdf"}
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Remove file from disk
        cls.report_file.delete()
