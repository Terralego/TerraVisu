from django.core.exceptions import ValidationError
from django.test import TestCase

from project.accounts.tests.factories import SuperUserFactory
from project.visu.admin import SheetBlockAdminForm
from project.visu.forms import FeatureSheetAdminForm
from project.visu.models import (
    SheetBlockType,
    SheetFieldType,
)
from project.visu.tests.factories import (
    FeatureSheetFactory,
    SheetFieldFactory,
    SheetFieldInlineFormSetFactory,
    SheetListFieldInlineFormSetFactory,
)


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
        cls.textual_field_2 = SheetFieldFactory(
            type=SheetFieldType.TEXTUAL, label="NumField"
        )
        cls.source_2 = cls.textual_field_2.field.source

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_admin_access(self):
        response = self.client.get("/config/")
        self.assertEqual(response.status_code, 200)


class SheetBlockAdminFormTest(AdminTestCase):
    def test_numerical_block_requires_numerical_fields(self):
        form = SheetBlockAdminForm(
            data={
                "sheet": self.feature_sheet,
                "type": SheetBlockType.RADAR_PLOT,
                "fields_source": self.source,
                "title": "Block title",
            }
        )
        # One non-numerical field included for a RADAR_PLOT => should raise
        formset_data = {
            "sheetfieldthroughmodel_set-TOTAL_FORMS": 1,
            "sheetfieldthroughmodel_set-INITIAL_FORMS": "0",
            "sheetfieldthroughmodel_set-MIN_NUM_FORMS": "0",
            "sheetfieldthroughmodel_set-MAX_NUM_FORMS": "1000",
            "sheetfieldthroughmodel_set-0-field": self.textual_field.pk,
        }
        self.assertTrue(form.is_valid(), form.errors)
        block = form.save()
        formset = SheetFieldInlineFormSetFactory(
            formset_data,
            instance=block,
            prefix="sheetfieldthroughmodel_set",
        )
        with self.assertRaises(ValidationError) as cm:
            formset.clean()
        exc = cm.exception
        self.assertIn("requires all fields to be NUMERICAL", str(exc))
        self.assertIn("TextField", str(exc))

    def test_boolean_block_requires_boolean_fields(self):
        form = SheetBlockAdminForm(
            data={
                "sheet": self.feature_sheet,
                "type": SheetBlockType.BOOLEANS,
                "fields_source": self.source,
                "title": "Block title",
            }
        )
        # One non-boolean field included for BOOLEANS => should raise
        formset_data = {
            "sheetfieldthroughmodel_set-TOTAL_FORMS": 1,
            "sheetfieldthroughmodel_set-INITIAL_FORMS": "0",
            "sheetfieldthroughmodel_set-MIN_NUM_FORMS": "0",
            "sheetfieldthroughmodel_set-MAX_NUM_FORMS": "1000",
            "sheetfieldthroughmodel_set-0-field": self.textual_field.pk,
        }

        self.assertTrue(form.is_valid(), form.errors)
        block = form.save()
        formset = SheetFieldInlineFormSetFactory(
            formset_data,
            instance=block,
            prefix="sheetfieldthroughmodel_set",
        )
        with self.assertRaises(ValidationError) as cm:
            formset.clean()
        exc = cm.exception
        self.assertIn("requires all fields to be BOOLEAN", str(exc))
        self.assertIn("TextField", str(exc))

    def test_field_from_wrong_source(self):
        form = SheetBlockAdminForm(
            data={
                "sheet": self.feature_sheet,
                "type": SheetBlockType.BOOLEANS,
                "fields_source": self.source,
                "title": "Block title",
            }
        )
        # One non-boolean field included for BOOLEANS => should raise
        formset_data = {
            "sheetfieldthroughmodel_set-TOTAL_FORMS": 1,
            "sheetfieldthroughmodel_set-INITIAL_FORMS": "0",
            "sheetfieldthroughmodel_set-MIN_NUM_FORMS": "0",
            "sheetfieldthroughmodel_set-MAX_NUM_FORMS": "1000",
            "sheetfieldthroughmodel_set-0-field": self.textual_field_2.pk,
        }

        self.assertTrue(form.is_valid(), form.errors)
        block = form.save()
        formset = SheetFieldInlineFormSetFactory(
            formset_data,
            instance=block,
            prefix="sheetfieldthroughmodel_set",
        )
        with self.assertRaises(ValidationError) as cm:
            formset.clean()
        exc = cm.exception
        self.assertIn(
            f"The following fields do not belong to the selected source: {self.textual_field_2.label}",
            str(exc),
        )

    def test_valid_numerical_block_passes(self):
        form = SheetBlockAdminForm(
            data={
                "sheet": self.feature_sheet,
                "type": SheetBlockType.BAR_PLOT,
                "fields_source": self.source,
                "title": "Block title",
            }
        )
        # Only numerical fields => should not raise
        formset_data = {
            "sheetfieldthroughmodel_set-TOTAL_FORMS": 1,
            "sheetfieldthroughmodel_set-INITIAL_FORMS": "0",
            "sheetfieldthroughmodel_set-MIN_NUM_FORMS": "0",
            "sheetfieldthroughmodel_set-MAX_NUM_FORMS": "1000",
            "sheetfieldthroughmodel_set-0-field": self.numerical_field_1.pk,
        }

        self.assertTrue(form.is_valid(), form.errors)
        block = form.save()
        formset = SheetFieldInlineFormSetFactory(
            formset_data,
            instance=block,
            prefix="sheetfieldthroughmodel_set",
        )
        self.assertTrue(formset.is_valid(), formset.errors)


class FeatureSheetAdminFormTest(AdminTestCase):
    def test_sheets_list_fields(self):
        form = FeatureSheetAdminForm(
            data={
                "name": "Test sheet",
                "sources": [self.source_2],
                "unique_identifier": self.textual_field_2.field,
            }
        )
        # One field from another source
        formset_data = {
            "sources": [self.source_2.pk],
            "sheetlistfieldthroughmodel_set-TOTAL_FORMS": 1,
            "sheetlistfieldthroughmodel_set-INITIAL_FORMS": "0",
            "sheetlistfieldthroughmodel_set-MIN_NUM_FORMS": "0",
            "sheetlistfieldthroughmodel_set-MAX_NUM_FORMS": "1000",
            "sheetlistfieldthroughmodel_set-0-list_field": self.textual_field.field.pk,
        }
        self.assertTrue(form.is_valid(), form.errors)
        sheet = form.save()
        formset = SheetListFieldInlineFormSetFactory(
            formset_data,
            instance=sheet,
            prefix="sheetlistfieldthroughmodel_set",
        )
        with self.assertRaises(ValidationError) as cm:
            formset.clean()
        exc = cm.exception
        self.assertIn(
            "Please choose fields that belong to one of the selected sources above.",
            str(exc),
        )

    def test_sheets_list_fields_from_several_sources(self):
        form = FeatureSheetAdminForm(
            data={
                "name": "Test sheet",
                "sources": [self.source_2],
                "unique_identifier": self.textual_field_2.field,
            }
        )
        # Fields from different sources
        formset_data = {
            "sources": [self.source_2.pk],
            "sheetlistfieldthroughmodel_set-TOTAL_FORMS": 2,
            "sheetlistfieldthroughmodel_set-INITIAL_FORMS": "0",
            "sheetlistfieldthroughmodel_set-MIN_NUM_FORMS": "0",
            "sheetlistfieldthroughmodel_set-MAX_NUM_FORMS": "1000",
            "sheetlistfieldthroughmodel_set-0-list_field": self.textual_field.field.pk,
            "sheetlistfieldthroughmodel_set-1-list_field": self.textual_field_2.field.pk,
        }
        self.assertTrue(form.is_valid(), form.errors)
        block = form.save()
        formset = SheetListFieldInlineFormSetFactory(
            formset_data,
            instance=block,
            prefix="sheetlistfieldthroughmodel_set",
        )
        with self.assertRaises(ValidationError) as cm:
            formset.clean()
        exc = cm.exception
        self.assertIn("These fields must all come from the same source.", str(exc))
