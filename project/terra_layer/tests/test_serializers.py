from django.test import TestCase

from project.geosource.models import Field
from project.geosource.tests.factories import PostGISSourceFactory
from project.terra_layer.serializers import LayerDetailSerializer


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
