from rest_framework import serializers

from .models import FeatureSheet, SheetBlock, SheetField


class SheetFieldSerializer(serializers.ModelSerializer):
    field_source = serializers.CharField(source="field.source", read_only=True)
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

    class Meta:
        model = SheetBlock
        fields = (
            "id",
            "title",
            "display_title",
            "type",
            "fields",
            "extra_fields",
            "text",
            "geom_field",
        )


class FeatureSheetSerializer(serializers.ModelSerializer):
    blocks = SheetBlockSerializer(read_only=True, many=True)
    accessible_from = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = FeatureSheet
        fields = ("id", "name", "unique_identifier", "blocks", "accessible_from")
