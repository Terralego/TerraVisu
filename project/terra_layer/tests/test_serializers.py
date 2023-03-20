from unittest.mock import MagicMock
from django.test import TestCase
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from project.geosource.models import Source
from project.terra_layer.serializers import LayerDetailSerializer, StyleImageSerializer
from project.terra_layer.models import StyleImage


class LayerDetailSerializerTestCase(TestCase):
    def test_create_layer_with_style_image(self):
        source = Source.objects.create(name="source test")
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00"
            b"\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00"
            b"\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        )
        layer_data = {
            "name": "test_layer",
            "source": source.pk,
            "style_images": [
                {
                    "name": "small.gif",
                    "file": SimpleUploadedFile("small.gif", content=small_gif, content_type="image/gif"),
                    "action": StyleImageSerializer.CREATE,
                },
            ],
        }

        serializer = LayerDetailSerializer(data=layer_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        layer = serializer.save()
        self.assertTrue(
            StyleImage.objects.filter(id=layer.style_images.first().id).exists()
        )
