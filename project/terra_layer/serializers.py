import json

from django.db import transaction
from django.utils.translation import gettext as _
from mapbox_baselayer.models import BaseLayerTile, MapBaseLayer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.reverse import reverse
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from .models import CustomStyle, FilterField, Layer, Scene


class SceneListSerializer(ModelSerializer):
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


class SceneDetailSerializer(ModelSerializer):
    slug = serializers.SlugField(required=False)
    icon = serializers.SerializerMethodField()

    def get_icon(self, obj):
        if obj.custom_icon:
            return obj.custom_icon.url

    class Meta:
        model = Scene
        fields = "__all__"
        extra_kwargs = {"baselayer": {"allow_empty": True}}

    def to_internal_value(self, data):
        baselayer = data.get("baselayer")

        if type(baselayer) is not str:
            return super().to_internal_value(data)

        querydict = data.copy()
        querydict.setlist("baselayer", json.loads(baselayer))
        return super().to_internal_value(querydict)


class FilterFieldSerializer(ModelSerializer):
    sourceFieldId = PrimaryKeyRelatedField(source="field", read_only=True)

    class Meta:
        model = FilterField
        exclude = ("layer",)


class CustomStyleSerializer(ModelSerializer):
    class Meta:
        model = CustomStyle
        exclude = ("layer",)


class LayerListSerializer(ModelSerializer):
    class Meta:
        model = Layer
        fields = ("id", "source", "group", "name", "order", "active_by_default")

    def to_representation(self, obj):
        return {
            **super().to_representation(obj),
            "view": obj.group.view.pk if obj.group else None,
        }


class LayerDetailSerializer(ModelSerializer):
    fields = FilterFieldSerializer(many=True, read_only=True, source="fields_filters")
    extra_styles = CustomStyleSerializer(many=True, read_only=True)
    group = PrimaryKeyRelatedField(read_only=True)

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)

        # Update m2m through field
        self._update_m2m_through(instance, "fields", FilterFieldSerializer)
        self._update_nested(instance, "extra_styles", CustomStyleSerializer)

        return instance

    def to_representation(self, obj):
        return {
            **super().to_representation(obj),
            "view": obj.group.view.pk if obj.group else None,
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        # Update m2m through field
        self._update_m2m_through(instance, "fields", FilterFieldSerializer)
        self._update_nested(instance, "extra_styles", CustomStyleSerializer)

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


class PublicMapBaseLayerSerializer(serializers.ModelSerializer):
    """Serializer used to provide quick select list in default public settings API endpoint"""

    tilejson_url = serializers.SerializerMethodField()

    def get_tilejson_url(self, instance):
        """
        Provide generated tilejson or mapbox url along base layer type
        """
        if instance.base_layer_type != "mapbox":
            return reverse("baselayer-tilejson", args=(instance.pk,))
        else:
            return instance.map_box_url

    class Meta:
        model = MapBaseLayer
        fields = ("id", "order", "name", "slug", "tilejson_url")
