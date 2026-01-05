from rest_framework import serializers

from project.visu.models import ExtraMenuItem, FeatureSheet, SheetBlock, SheetField


class ExtraMenuItemSerializer(serializers.ModelSerializer):
    id = serializers.SlugField()

    class Meta:
        model = ExtraMenuItem
        fields = ("id", "label", "href", "icon")


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

    class Meta:
        model = SheetBlock
        fields = (
            "id",
            "title",
            "display_title",
            "type",
            "fields",
            "text",
            "geom_field",
        )


class FeatureSheetSerializer(serializers.ModelSerializer):
    blocks = SheetBlockSerializer(read_only=True, many=True)
    accessible_from = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = FeatureSheet
        fields = ("id", "name", "unique_identifier", "blocks", "accessible_from")
