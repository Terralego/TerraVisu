import inspect
import sys

from django.utils.functional import cached_property
from rest_framework import serializers

from project.geosource.models import Source, WMTSSource

DEFAULT_SOURCE_NAME = "terra"


class SourceSerializer(serializers.BaseSerializer):
    @classmethod
    def get_object_serializer(cls, obj):

        source = obj.source.get_real_instance()
        clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)

        for _, serializer in clsmembers:
            if (
                serializer.__module__ == __name__
                and serializer.Meta.model is source.__class__
            ):
                return serializer(obj)

        return cls(obj)

    @cached_property
    def source_object(self):
        return self.instance.source.get_real_instance()

    def to_representation(self, obj):
        return {
            **obj.map_style,
            "id": obj.layer_identifier,
            "source": DEFAULT_SOURCE_NAME,
            "source-layer": self.source_object.slug,
        }

    class Meta:
        model = Source


class WMTSSourceSerializer(SourceSerializer):
    def to_representation(self, obj):
        return {
            **obj.map_style,
            "id": obj.layer_identifier,
            "type": "raster",
            "minzoom": self.source_object.minzoom or 0,
            "maxzoom": self.source_object.maxzoom or 24,
            "source": {
                "type": "raster",
                "tileSize": self.source_object.tile_size,
                "tiles": [self.source_object.url],
            },
        }

    class Meta:
        model = WMTSSource
