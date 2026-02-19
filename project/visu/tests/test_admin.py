from django.core.exceptions import ValidationError
from django.test import TestCase

from project.accounts.tests.factories import SuperUserFactory
from project.visu.admin import SheetBlockAdminForm
from project.visu.models import SheetBlockType, SheetFieldType
from project.visu.tests.factories import FeatureSheetFactory, SheetFieldFactory


class AdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()
        cls.textual_field = SheetFieldFactory(
            type=SheetFieldType.TEXTUAL, label="TextField"
        )
        cls.source = cls.textual_field.field.source
        cls.numerical_field_1 = SheetFieldFactory(
            type=SheetFieldType.NUMERICAL, label="NumField"
        )
        cls.numerical_field_2 = SheetFieldFactory(
            type=SheetFieldType.NUMERICAL, label="NumField"
        )
        # Change fields source for test coherence
        field = cls.numerical_field_1.field
        field.source = cls.source
        field.save()
        field = cls.numerical_field_2.field
        field.source = cls.source
        field.save()
        cls.feature_sheet = FeatureSheetFactory(sources=[cls.source])

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_admin_access(self):
        response = self.client.get("/config/")
        self.assertEqual(response.status_code, 200)


class SheetBlockAdminFormTest(AdminTestCase):
    def test_numerical_block_requires_numerical_fields(self):
        form = SheetBlockAdminForm()
        # One non-numerical field included for a RADAR_PLOT => should raise
        form.cleaned_data = {
            "sheet": self.feature_sheet,
            "type": SheetBlockType.RADAR_PLOT,
            "fields": [self.textual_field],
            "fields_source": self.source,
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
        form.cleaned_data = {
            "sheet": self.feature_sheet,
            "type": SheetBlockType.BOOLEANS,
            "fields": [self.numerical_field_1],
            "fields_source": self.source,
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
        form.cleaned_data = {
            "sheet": self.feature_sheet,
            "type": SheetBlockType.BAR_PLOT,
            "fields": [self.numerical_field_1, self.numerical_field_2],
            "fields_source": self.source,
            "extra_fields": [],
        }
        cleaned = form.clean()
        self.assertEqual(cleaned.get("type"), SheetBlockType.BAR_PLOT)
