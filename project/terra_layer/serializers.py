import json
import mimetypes

import magic
from django.db import transaction
from django.utils.translation import gettext as _
from drf_extra_fields.fields import Base64ImageField
from mapbox_baselayer.models import BaseLayerTile, MapBaseLayer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.reverse import reverse

from project.geosource.models import Field

from .models import (
    CustomStyle,
    FilterField,
    Layer,
    Report,
    ReportConfig,
    ReportField,
    ReportFile,
    Scene,
    StyleImage,
)


class SceneListSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source="get_absolute_url", read_only=True)
    layers_tree_url = SerializerMethodField()

    def get_layers_tree_url(self, obj):
        return reverse("layerview", args=[obj.slug])

    class Meta:
        model = Scene
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "custom_icon",
            "url",
            "layers_tree_url",
            "order",
        )


class SceneDetailSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)
    baselayer = serializers.PrimaryKeyRelatedField(
        queryset=MapBaseLayer.objects.all(), source="base_layers", many=True
    )  # compat with old name of m2m attribute. to fix in admin.

    class Meta:
        model = Scene
        exclude = ("base_layers",)
        extra_kwargs = {"baselayer": {"allow_empty": True}}

    def to_internal_value(self, data):
        baselayer = data.get("baselayer")

        if type(baselayer) is not str:
            return super().to_internal_value(data)

        querydict = data.copy()
        querydict.setlist("baselayer", json.loads(baselayer))
        return super().to_internal_value(querydict)


class FilterFieldSerializer(serializers.ModelSerializer):
    sourceFieldId = serializers.PrimaryKeyRelatedField(source="field", read_only=True)

    class Meta:
        model = FilterField
        exclude = ("layer",)


class CustomStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomStyle
        exclude = ("layer",)


class StyleImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    data = Base64ImageField(required=False, source="file", write_only=True)

    class Meta:
        model = StyleImage
        exclude = ("layer",)
        read_only_fields = ("slug", "file")


class ReportFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = ReportFile
        fields = ["file"]

    def validate_file(self, value):
        max_size = 5 * 1024 * 1024  # 5 MB
        if value.size > max_size:
            big_file_message = "File size cannot exceed 5MB"
            raise serializers.ValidationError(big_file_message)
        # Check for allowed extensions in filename
        allowed_extensions = [".jpg", ".jpeg", ".png", ".pdf", ".zip"]
        wrong_extension_message = (
            f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
        file_extension = value.name.lower().split(".")[-1]
        if f".{file_extension}" not in allowed_extensions:
            raise serializers.ValidationError(wrong_extension_message)
        # Check for allowed extensions in file content
        value.seek(0)
        file_mimetype = magic.from_buffer(value.read(), mime=True)
        file_mimetype_allowed = f".{file_extension}" in mimetypes.guess_all_extensions(
            file_mimetype
        )
        if not file_mimetype_allowed:
            raise ValidationError(wrong_extension_message)
        return value


class ReportSerializer(serializers.ModelSerializer):
    files = ReportFileSerializer(many=True, required=False)

    class Meta:
        model = Report
        fields = ["config", "feature", "layer", "content", "files"]

    def create(self, validated_data):
        files = []
        if "files" in self.initial_data:
            files = self.initial_data.pop("files", [])
        if len(files) > 3:
            too_many_files_message = "This request cannot contain more than 3 files."
            raise serializers.ValidationError(too_many_files_message)
        report = super().create(validated_data)
        # Create ReportFile instances for each uploaded file
        for file in files:
            obj = ReportFileSerializer(
                data={
                    "file": file,
                }
            )
            if obj.is_valid(raise_exception=True):
                obj.save(report=report)
        return report


class ReportFieldSerializer(serializers.ModelSerializer):
    sourceFieldId = serializers.PrimaryKeyRelatedField(
        source="field", queryset=Field.objects.all()
    )

    class Meta:
        model = ReportField
        fields = ("id", "order", "sourceFieldId")


class ReportConfigSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    report_fields = ReportFieldSerializer(many=True)

    class Meta:
        model = ReportConfig
        fields = ("id", "label", "report_fields")


class LayerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ("id", "source", "group", "name", "order", "active_by_default")

    def to_representation(self, obj):
        return {
            **super().to_representation(obj),
            "view": obj.group.view.pk if obj.group else None,
        }


class LayerComparaison(serializers.ModelSerializer):
    field = serializers.PrimaryKeyRelatedField(
        source="compare_field", queryset=Field.objects.all()
    )
    url = serializers.URLField(source="compare_url")
    separator = serializers.CharField(source="compare_separator")

    class Meta:
        model = Layer
        fields = ("url", "field", "separator")


class LayerDetailSerializer(serializers.ModelSerializer):
    fields = FilterFieldSerializer(many=True, read_only=True, source="fields_filters")
    extra_styles = CustomStyleSerializer(many=True, read_only=True)
    group = serializers.PrimaryKeyRelatedField(read_only=True)
    style_images = StyleImageSerializer(many=True, read_only=False, required=False)
    report_configs = ReportConfigSerializer(many=True, read_only=False, required=False)
    comparaison = LayerComparaison(required=False)

    @property
    def validated_data(self):
        data = super().validated_data
        if "comparaison" in data:
            comparaison_data = data.pop("comparaison")
            if comparaison_data:
                data["compare_url"] = comparaison_data["compare_url"]
                data["compare_field"] = comparaison_data["compare_field"]
                data["compare_separator"] = comparaison_data["compare_separator"]
        return data

    @transaction.atomic
    def create(self, validated_data):
        style_images = validated_data.pop("style_images", [])
        report_configs = validated_data.pop("report_configs", [])
        instance = super().create(validated_data)
        for image_data in style_images:
            StyleImage.objects.create(layer=instance, **image_data)

        # Update m2m through field
        self._update_m2m_through(instance, "fields", FilterFieldSerializer)
        self._update_nested(instance, "extra_styles", CustomStyleSerializer)
        # Handle nested ReportConfig(s)
        self._create_or_update_report_configs(instance, report_configs)

        instance.save()

        return instance

    def to_representation(self, obj):
        return {
            **super().to_representation(obj),
            "view": obj.group.view.pk if obj.group else None,
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        style_images = validated_data.pop("style_images", [])
        report_configs = validated_data.pop("report_configs", [])
        instance = super().update(instance, validated_data)

        # Delete first
        image_ids = [image["id"] for image in style_images if image.get("id")]
        instance.style_images.exclude(id__in=image_ids).delete()
        for image_data in style_images:
            if not image_data.get("id"):
                StyleImage.objects.create(layer=instance, **image_data)
            else:
                style_image_id = image_data.pop("id")
                style_image = instance.style_images.get(id=style_image_id)
                style_image.name = image_data.get("name")
                if image_data.get("file"):
                    style_image.file = image_data.get("file")
                style_image.save()

        # Update m1m through field
        self._update_m2m_through(instance, "fields", FilterFieldSerializer)
        self._update_nested(instance, "extra_styles", CustomStyleSerializer)
        # Handle nested ReportConfig(s)
        self._create_or_update_report_configs(instance, report_configs)

        instance.save()

        return instance

    def _update_nested(self, instance, field, serializer):
        getattr(instance, field).all().delete()

        for value in self.initial_data.get(field, []):
            obj = serializer(data=value)
            if obj.is_valid(raise_exception=True):
                obj.save(layer=instance)

    def _update_m2m_through(self, instance, field, serializer):
        getattr(instance, field).clear()

        for index, value in enumerate(self.initial_data.get(field, [])):
            value["order"] = index  # Add order field

            obj = serializer(data=value)
            if obj.is_valid(raise_exception=True):
                obj.save(layer=instance)

    def update_report_fields(self, report_config, report_fields):
        report_config.report_fields.all().delete()
        for report_field_data in report_fields:
            ReportField.objects.create(
                field=report_field_data["field"],
                order=report_field_data["order"],
                config=report_config,
            )

    def _create_or_update_report_configs(self, instance, report_configs):
        for report_config_data in report_configs:
            config_pk = report_config_data.pop("id", None)
            # For update
            if (
                config_pk
                and ReportConfig.objects.filter(pk=config_pk, layer=instance).exists()
            ):
                existing_config = ReportConfig.objects.get(pk=config_pk, layer=instance)
                existing_config.label = report_config_data["label"]
                existing_config.save()
                self.update_report_fields(
                    existing_config, report_config_data["report_fields"]
                )
            # For create
            else:
                new_report_config = ReportConfig.objects.create(
                    label=report_config_data["label"], layer=instance
                )
                self.update_report_fields(
                    new_report_config, report_config_data["report_fields"]
                )

    class Meta:
        model = Layer
        fields = "__all__"


class BaseLayerTileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseLayerTile
        fields = ("url",)

    def to_representation(self, instance):
        return instance.url

    def to_internal_value(self, data):
        return data


class MapBaseLayerSerializer(serializers.ModelSerializer):
    tiles = BaseLayerTileSerializer(many=True, required=False)
    tilejson_url = serializers.SerializerMethodField()

    def get_tilejson_url(self, instance):
        """
        Provide generated tilejson or mapbox url along base layer type
        """
        if instance.base_layer_type != "mapbox":
            return reverse(
                "baselayer-tilejson",
                args=(instance.pk,),
                request=self.context.get("request"),
            )
        else:
            return instance.map_box_url

    def validate(self, attrs):
        if attrs.get("base_layer_type") == "mapbox":
            if attrs.get("tiles"):
                raise ValidationError(
                    _("'tiles' should not be filled for mapbox base layers.")
                )
            if not attrs.get("map_box_url"):
                raise ValidationError(
                    _("'map_box_url' should be filled for mapbox base layers.")
                )
        else:
            if not attrs.get("tiles"):
                raise ValidationError(
                    _("'tiles' should be filled for raster and vector base layers.")
                )
            if attrs.get("map_box_url"):
                raise ValidationError(
                    _(
                        "'map_box_url' should not be filled for raster and vector base layers."
                    )
                )
        return attrs

    def create(self, validated_data):
        """handle sub tile definition"""
        tiles = validated_data.pop("tiles", [])
        instance = MapBaseLayer.objects.create(**validated_data)
        for tile in tiles:
            BaseLayerTile.objects.create(base_layer=instance, url=tile)
        return instance

    def update(self, instance, validated_data):
        """handle sub tile definition"""
        tiles = validated_data.pop("tiles", [])
        for key, value in validated_data.items():
            # update data for each instance validated value
            setattr(instance, key, value)
        if tiles:
            # delete tiles not in putted data
            instance.tiles.exclude(url__in=[tile for tile in tiles]).delete()
            tile_instances = [
                BaseLayerTile.objects.get_or_create(url=tile, base_layer=instance)[0]
                for tile in tiles
            ]
            instance.tiles.set(tile_instances)
        instance.save()
        return instance

    class Meta:
        model = MapBaseLayer
        fields = (
            "id",
            "tiles",
            "name",
            "order",
            "slug",
            "base_layer_type",
            "map_box_url",
            "sprite",
            "glyphs",
            "min_zoom",
            "max_zoom",
            "tile_size",
            "attribution",
            "tiles",
            "tilejson_url",
        )
