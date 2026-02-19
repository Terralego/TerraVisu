from rest_framework import serializers

from project.visu.models import ExtraMenuItem

from ..geosource.models import Source
from .models import FeatureSheet, SheetBlock, SheetField


class SourceGeometrySerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="slug", read_only=True)
    geom_field = serializers.SerializerMethodField()

    class Meta:
        model = Source
        fields = (
            "source",
            "geom_field",
        )

    def get_geom_field(self, instance):
        return instance.SOURCE_GEOM_ATTRIBUTE


class OrderFieldSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.slug", read_only=True)
    field = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = Source
        fields = (
            "source",
            "field",
        )


class SheetFieldSerializer(serializers.ModelSerializer):
    field_source = serializers.CharField(source="field.source.slug", read_only=True)
    field_name = serializers.CharField(source="field.name", read_only=True)

    class Meta:
        model = SheetField
        fields = (
            "id",
            "label",
            "field_source",
            "field_name",
            "description",
            "type",
            "suffix",
            "decimals",
            "picto_true",
            "picto_false",
        )


class SheetBlockSerializer(serializers.ModelSerializer):
    fields = SheetFieldSerializer(read_only=True, many=True)
    extra_fields = SheetFieldSerializer(read_only=True, many=True)
    first_geom_source = SourceGeometrySerializer(read_only=True)
    second_geom_source = SourceGeometrySerializer(read_only=True)
    order_field = OrderFieldSerializer(read_only=True)
    fields_source = serializers.CharField(source="fields_source.slug", read_only=True)

    class Meta:
        model = SheetBlock
        fields = (
            "id",
            "title",
            "display_title",
            "type",
            "fields_source",
            "fields",
            "first_geom_source",
            "second_geom_source",
            "extra_fields",
            "order_field",
            "limit",
            "text",
        )


class ExtraMenuItemSerializer(serializers.ModelSerializer):
    id = serializers.SlugField()

    class Meta:
        model = ExtraMenuItem
        fields = ("id", "label", "href", "icon")


class FeatureSheetSerializer(serializers.ModelSerializer):
    blocks = SheetBlockSerializer(read_only=True, many=True)
    sources = serializers.SlugRelatedField(slug_field="slug", read_only=True, many=True)
    unique_identifier = serializers.CharField(
        source="unique_identifier.name", read_only=True
    )

    class Meta:
        model = FeatureSheet
        fields = ("id", "name", "unique_identifier", "blocks", "sources")
