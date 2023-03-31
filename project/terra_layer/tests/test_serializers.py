import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from project.geosource.models import Source
from project.terra_layer.models import Layer, StyleImage
from project.terra_layer.serializers import LayerDetailSerializer


class LayerDetailSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00"
            b"\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00"
            b"\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        )

    def test_create_layer_with_style_image(self):
        source = Source.objects.create(name="source test")
        image = base64.b64encode(self.small_gif)
        layer_data = {
            "name": "test_layer",
            "source": source.pk,
            "style_images": [
                {
                    "name": "small.gif",
                    "data": f"data:image/gif;base64,{image.decode('UTF-8')}",
                },
            ],
        }

        serializer = LayerDetailSerializer(data=layer_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        layer = serializer.save()
        self.assertTrue(
            StyleImage.objects.filter(id=layer.style_images.first().id).exists()
        )

    def test_create_style_image_when_updating_layer(self):
        source = Source.objects.create(name="source test")
        layer = Layer.objects.create(name="test layer", source=source)
        self.assertEqual(layer.style_images.count(), 0)
        image = base64.b64encode(self.small_gif)
        layer_data = {
            "id": layer.id,
            "name": layer.name,
            "source": source.id,
            "style_images": [
                {
                    "name": "small.gif",
                    "data": f"data:image/gif;base64,{image.decode('UTF-8')}",
                }
            ],
        }
        serializer = LayerDetailSerializer(data=layer_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(
            StyleImage.objects.filter(id=instance.style_images.first().id).count(), 1
        )

    def test_update_image_when_updating_layer(self):
        source = Source.objects.create(name="source test")
        layer = Layer.objects.create(name="test layer", source=source)
        style_image = StyleImage.objects.create(
            name="small.gif",
            file=SimpleUploadedFile(
                "small.gif", content=self.small_gif, content_type="image/gif"
            ),
            layer=layer,
        )
        image = base64.b64encode(self.small_gif)
        layer_data = {
            "id": layer.id,
            "name": layer.name,
            "source": source.id,
            "style_images": [
                {
                    "id": style_image.id,
                    "name": "really_small.gif",
                    "data": f"data:image/gif;base64,{image.decode('UTF-8')}",
                }
            ],
        }
        serializer = LayerDetailSerializer(layer, data=layer_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        style_image.refresh_from_db()
        self.assertEqual(style_image.name, "really_small.gif")

    def test_delete_image_when_updating_layer(self):
        source = Source.objects.create(name="source test")
        layer = Layer.objects.create(name="test layer", source=source)
        style_image = StyleImage.objects.create(
            name="small.gif",
            file=SimpleUploadedFile(
                "small.gif", content=self.small_gif, content_type="image/gif"
            ),
            layer=layer,
        )
        layer_data = {
            "id": layer.id,
            "name": layer.name,
            "source": source.id,
            "style_images": [],
        }
        serializer = LayerDetailSerializer(layer, data=layer_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertFalse(StyleImage.objects.filter(id=style_image.id).exists())
