from unittest import mock

from django.contrib.gis.geos import Point
from django.test import TestCase
from geostore.models import Feature, Layer

from project.geo_api.serializers import FeatureGeoSerializer, FeatureListSerializer


class FeatureSerializersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.layer = Layer.objects.create(name="test_layer")
        cls.feature = Feature.objects.create(
            layer=cls.layer,
            geom=Point(1.0, 43.0),
            identifier="feat-1",
            properties={"name": "Toulouse", "pop": 500000, "code": "31000"},
        )

    def test_feature_list_serializer_without_selected_fields(self):
        serializer = FeatureListSerializer(self.feature)
        data = serializer.data
        self.assertEqual(data["identifier"], "feat-1")
        self.assertEqual(
            data["properties"], {"name": "Toulouse", "pop": 500000, "code": "31000"}
        )
        self.assertNotIn("geom", data)

    def test_feature_list_serializer_with_selected_fields(self):
        context = {"selected_fields": ["name", "code"]}
        serializer = FeatureListSerializer(self.feature, context=context)
        data = serializer.data
        self.assertEqual(data["properties"], {"name": "Toulouse", "code": "31000"})
        self.assertNotIn("pop", data["properties"])

    def test_feature_list_serializer_with_non_dict_properties(self):
        context = {"selected_fields": ["name"]}
        serializer = FeatureListSerializer(context=context)
        with mock.patch(
            "geostore.serializers.FeatureSerializer.to_representation",
            return_value={"id": 1, "identifier": "f1", "properties": "not_a_dict"},
        ):
            data = serializer.to_representation(self.feature)
            self.assertEqual(data["properties"], "not_a_dict")

    def test_feature_geo_serializer_without_selected_fields(self):
        serializer = FeatureGeoSerializer(self.feature)
        data = serializer.data
        self.assertEqual(data["type"], "Feature")
        self.assertEqual(data["geometry"]["type"], "Point")
        self.assertEqual(
            data["properties"], {"name": "Toulouse", "pop": 500000, "code": "31000"}
        )

    def test_feature_geo_serializer_with_selected_fields(self):
        context = {"selected_fields": ["pop"]}
        serializer = FeatureGeoSerializer(self.feature, context=context)
        data = serializer.data
        self.assertEqual(data["properties"], {"pop": 500000})
        self.assertNotIn("name", data["properties"])
