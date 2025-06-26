from django.test import TestCase

from project.accounts.tests.factories import SuperUserFactory
from project.geosource.models import FieldTypes
from project.terra_layer.models import ReportField
from project.terra_layer.tests.factories import LayerFactory, ReportFactory


class LayerAdminTesCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        LayerFactory.create_batch(10)
        cls.user = SuperUserFactory.create()
        cls.report = ReportFactory.create(user=cls.user)
        field = cls.report.config.layer.source.fields.create(
            name="test_field", label="test_label", data_type=FieldTypes.String.value
        )
        cls.report_field = ReportField.objects.create(
            config=cls.report.config,
            order=1,
            field=field,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_list(self):
        response = self.client.get("/debug/terra_layer/layer/")
        self.assertEqual(response.status_code, 200)

    def test_report_list(self):
        response = self.client.get("/debug/terra_layer/report/")
        self.assertEqual(response.status_code, 200)

    def test_reportconfig_list(self):
        response = self.client.get("/debug/terra_layer/reportconfig/")
        self.assertEqual(response.status_code, 200)

    def test_reportfield_list(self):
        response = self.client.get("/debug/terra_layer/reportfield/")
        self.assertEqual(response.status_code, 200)
