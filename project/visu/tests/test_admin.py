from django.core.exceptions import ValidationError
from django.test import TestCase

from project.accounts.tests.factories import SuperUserFactory
from project.visu.admin import SheetBlockAdminForm
from project.visu.models import SheetBlockType, SheetFieldType
from project.visu.tests.factories import SheetFieldFactory


class AdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_admin_access(self):
        response = self.client.get("/config/")
        self.assertEqual(response.status_code, 200)


class SheetBlockAdminFormTest(TestCase):
    def test_numerical_block_requires_numerical_fields(self):
        form = SheetBlockAdminForm()
        # One non-numerical field included for a RADAR_PLOT => should raise
        textual_field = SheetFieldFactory(
            type=SheetFieldType.TEXTUAL, label="TextField"
        )

        form.cleaned_data = {
            "type": SheetBlockType.RADAR_PLOT,
            "fields": [textual_field],
            "extra_fields": [],
        }
        with self.assertRaises(ValidationError) as cm:
            form.clean()
        exc = cm.exception
        self.assertIn("requires all fields to be NUMERICAL", str(exc))
        self.assertIn("TextField", str(exc))

    def test_boolean_block_requires_boolean_fields(self):
        form = SheetBlockAdminForm()
        # One non-boolean field included for BOOLEANS => should raise
        numerical_field = SheetFieldFactory(
            type=SheetFieldType.NUMERICAL, label="NumField"
        )

        form.cleaned_data = {
            "type": SheetBlockType.BOOLEANS,
            "fields": [numerical_field],
            "extra_fields": [],
        }
        with self.assertRaises(ValidationError) as cm:
            form.clean()
        exc = cm.exception
        self.assertIn("requires all fields to be BOOLEAN", str(exc))
        self.assertIn("NumField", str(exc))

    def test_valid_numerical_block_passes(self):
        form = SheetBlockAdminForm()
        # Only numerical fields => should not raise and should return cleaned_data
        num_field1 = SheetFieldFactory(type=SheetFieldType.NUMERICAL, label="Num1")
        num_field2 = SheetFieldFactory(type=SheetFieldType.NUMERICAL, label="Num2")

        form.cleaned_data = {
            "type": SheetBlockType.BAR_PLOT,
            "fields": [num_field1, num_field2],
            "extra_fields": [],
        }
        cleaned = form.clean()
        self.assertEqual(cleaned.get("type"), SheetBlockType.BAR_PLOT)
