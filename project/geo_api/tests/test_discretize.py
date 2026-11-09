from unittest import mock

from django.contrib.gis.geos import Point
from django.test import TestCase
from geostore.models import Feature, Layer
from rest_framework.test import APIRequestFactory

from project.geo_api.views.discretize import (
    MAX_CLASSES,
    _parse_classes,
    _parse_manual_breaks,
)
from project.geo_api.views.feature_viewset import FeatureViewSet


class DiscretizeUnitTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.layer = Layer.objects.create(name="disc_layer")
        for i in range(1, 11):
            Feature.objects.create(
                layer=cls.layer,
                geom=Point(float(i), float(i)),
                identifier=f"feat-{i}",
                properties={"val": i * 10},
            )
        cls.factory = APIRequestFactory()

    def test_parse_classes(self):
        self.assertEqual(_parse_classes("5"), 5)
        self.assertEqual(_parse_classes(10), 10)
        self.assertIsNone(_parse_classes("abc"))
        self.assertIsNone(_parse_classes("0"))
        self.assertIsNone(_parse_classes("-5"))
        self.assertIsNone(_parse_classes(str(MAX_CLASSES + 1)))

    def test_parse_manual_breaks(self):
        self.assertIsNone(_parse_manual_breaks(""))
        self.assertIsNone(_parse_manual_breaks("   "))
        self.assertIsNone(_parse_manual_breaks("10,abc,30"))
        self.assertIsNone(_parse_manual_breaks("10"))
        self.assertIsNone(_parse_manual_breaks("30,20,10"))
        self.assertIsNone(_parse_manual_breaks("10,10,20"))
        self.assertEqual(_parse_manual_breaks("10, 20.5, 30"), [10.0, 20.5, 30.0])

    def test_discretize_invalid_classes(self):
        view = FeatureViewSet.as_view({"get": "discretize"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/discretize/val/?classes=invalid"
        )
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 400)
        self.assertIn("classes must be an integer", res.data["error"])

    def test_discretize_manual_missing_breaks(self):
        view = FeatureViewSet.as_view({"get": "discretize"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/discretize/val/?method=manual"
        )
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 400)
        self.assertIn("breaks parameter is required", res.data["error"])

    def test_discretize_manual_invalid_breaks(self):
        view = FeatureViewSet.as_view({"get": "discretize"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/discretize/val/?method=manual&breaks=10,5"
        )
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 400)
        self.assertIn("invalid breaks parameter", res.data["error"])

    def test_discretize_manual_valid(self):
        view = FeatureViewSet.as_view({"get": "discretize"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/discretize/val/?method=manual&breaks=10,50,100"
        )
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["breaks"], [10.0, 50.0, 100.0])
        self.assertEqual(len(res.data["entitiesByClass"]), 2)
        self.assertIn("stats", res.data)

    def test_discretize_standard_method_success(self):
        view = FeatureViewSet.as_view({"get": "discretize"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/discretize/val/?method=equal_interval&classes=3"
        )
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data["breaks"]) >= 2)
        self.assertEqual(len(res.data["entitiesByClass"]), 3)

    def test_discretize_method_unknown_value_error(self):
        view = FeatureViewSet.as_view({"get": "discretize"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/discretize/val/?method=unknown_method"
        )
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 400)

    def test_discretize_fallback_and_padding_classes(self):
        view = FeatureViewSet.as_view({"get": "discretize"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/discretize/val/?method=jenks&classes=5"
        )
        with mock.patch(
            "project.geo_api.views.discretize._discretize", return_value=None
        ):
            res = view(req, layer=str(self.layer.pk), field="val")
            self.assertEqual(res.status_code, 200)
            # fallback used min and max, padded to 5 classes
            self.assertEqual(len(res.data["entitiesByClass"]), 5)
            self.assertEqual(len(res.data["breaks"]), 6)
