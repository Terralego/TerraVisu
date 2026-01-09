from django.urls import reverse
from rest_framework.test import APITestCase

from project.accounts.tests.factories import SuperUserFactory
from project.terra_layer.tests.factories import LayerFactory

from ..models import ExtraSheetFieldThroughModel, SheetFieldThroughModel, SheetFieldType
from .factories import FeatureSheetFactory, SheetBlockFactory, SheetFieldFactory


class SheetFieldAdminTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = SuperUserFactory()
        cls.layer = LayerFactory(name="My Layer")
        cls.sheet = FeatureSheetFactory(
            name="My Test Sheet", accessible_from=[cls.layer]
        )
        cls.field_1 = SheetFieldFactory(
            label="My Test Field 1", type=SheetFieldType.BOOLEAN
        )
        cls.field_2 = SheetFieldFactory(
            label="My Test Field 2",
        )
        cls.block = SheetBlockFactory(
            title="My Test Block",
            sheet=cls.sheet,
            fields=[cls.field_1, cls.field_2],
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_feature_sheet_admin_list(self):
        url = reverse("config_site:feature_sheet_featuresheet_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Layer")
        self.assertContains(response, "My Test Sheet")
        self.assertEqual(str(self.sheet), "My Test Sheet")

    def test_sheet_block_admin_list(self):
        url = reverse("config_site:feature_sheet_sheetblock_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Test Block")
        self.assertContains(response, "My Test Field 1, My Test Field 2")
        self.assertEqual(str(self.block), "My Test Block")
        self.assertEqual(str(self.field_1), "My Test Field 1")

    def test_sheet_field_admin_list(self):
        url = reverse("config_site:feature_sheet_sheetfield_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Test Field 1")
        self.assertContains(response, "My Test Field 2")
        self.assertEqual(str(self.block), "My Test Block")

    def test_through_models(self):
        through_model_1 = SheetFieldThroughModel.objects.create(
            block=self.block, field=self.field_1
        )
        through_model_2 = ExtraSheetFieldThroughModel.objects.create(
            block=self.block, extra_field=self.field_2
        )
        self.assertEqual(str(through_model_1), "My Test Field 1")
        self.assertEqual(str(through_model_2), "My Test Field 2")
