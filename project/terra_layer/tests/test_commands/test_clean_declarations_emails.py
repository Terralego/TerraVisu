from io import StringIO
from unittest import mock

import freezegun
from django.core.management import call_command
from django.test import TestCase

from project.terra_layer.tests.factories import UnauthentifiedDeclarationFactory


class CleanDeclarationEmailsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.declaration = UnauthentifiedDeclarationFactory()

    @freezegun.freeze_time("2070-01-01 00:00:00")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_command_cleans_declarations_emails(self, mock_stdout):
        self.assertEqual(self.declaration.email, "test@email.fr")
        call_command("clean_declarations_emails")
        self.declaration.refresh_from_db()
        self.assertEqual(self.declaration.email, "")
        self.assertIn("Cleared email field for 1 declarations", mock_stdout.getvalue())
