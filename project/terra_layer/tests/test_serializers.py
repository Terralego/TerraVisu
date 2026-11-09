import json

from django.http import QueryDict
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from project.geosource.models import CommandSource, Field
from project.geosource.tests.factories import PostGISSourceFactory
from project.terra_layer.models import Layer
from project.terra_layer.serializers import (
    LayerDetailSerializer,
    MapBaseLayerSerializer,
    SceneDetailSerializer,
)
from project.terra_layer.sources_serializers import SourceSerializer


class LayerDetailSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = PostGISSourceFactory()

    def test_create_with_comparaison_data(self):
        field = Field.objects.create(name="test_field", source=self.source)
        comparaison_data = {
            "url": "https://test.com/?compare=",
            "field": field.pk,
            "separator": "+",
        }
        layer_data = {
            "name": "test_layer",
            "source": self.source.pk,
            "comparaison": comparaison_data,
        }

        serializer = LayerDetailSerializer(data=layer_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        layer = serializer.save()

        self.assertEqual(layer.compare_url, comparaison_data["url"])
        self.assertEqual(layer.compare_field_id, comparaison_data["field"])
        self.assertEqual(layer.compare_separator, comparaison_data["separator"])


class SceneDetailSerializerTestCase(TestCase):
    def test_to_internal_value_with_str_baselayer_querydict(self):
        ser = SceneDetailSerializer()
        qd = QueryDict(mutable=True)
        qd.setlist("name", ["Scene 1"])
        qd.setlist("baselayer", [json.dumps([])])
        val = ser.to_internal_value(qd)
        self.assertEqual(val["name"], "Scene 1")
        self.assertEqual(val["base_layers"], [])


class MapBaseLayerSerializerValidationTestCase(TestCase):
    def test_mapbox_with_tiles_raises_error(self):
        ser = MapBaseLayerSerializer()
        with self.assertRaises(ValidationError) as cm:
            ser.validate(
                {
                    "base_layer_type": "mapbox",
                    "tiles": ["http://tile"],
                    "map_box_url": "mapbox://...",
                }
            )
        self.assertIn("'tiles' should not be filled", str(cm.exception))

    def test_mapbox_without_map_box_url_raises_error(self):
        ser = MapBaseLayerSerializer()
        with self.assertRaises(ValidationError) as cm:
            ser.validate({"base_layer_type": "mapbox"})
        self.assertIn("'map_box_url' should be filled", str(cm.exception))

    def test_raster_without_tiles_raises_error(self):
        ser = MapBaseLayerSerializer()
        with self.assertRaises(ValidationError) as cm:
            ser.validate({"base_layer_type": "raster"})
        self.assertIn("'tiles' should be filled", str(cm.exception))

    def test_raster_with_map_box_url_raises_error(self):
        ser = MapBaseLayerSerializer()
        with self.assertRaises(ValidationError) as cm:
            ser.validate(
                {
                    "base_layer_type": "raster",
                    "tiles": ["http://tile"],
                    "map_box_url": "mapbox://...",
                }
            )
        self.assertIn("'map_box_url' should not be filled", str(cm.exception))


class SourcesSerializerFallbackTestCase(TestCase):
    def test_get_object_serializer_fallback_to_base_serializer(self):
        source = CommandSource.objects.create(name="cmd_src", command="cmd")
        layer = Layer(name="cmd_layer", source=source)
        ser = SourceSerializer.get_object_serializer(layer)
        self.assertIs(type(ser), SourceSerializer)
