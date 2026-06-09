from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from geostore.models import Feature


class FeatureListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ("id", "identifier", "properties")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        selected_fields = self.context.get("selected_fields")
        if selected_fields and isinstance(data.get("properties"), dict):
            data["properties"] = {
                k: v for k, v in data["properties"].items() if k in selected_fields
            }
        return data


class FeatureGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Feature
        geo_field = "geom"
        fields = ("id", "identifier", "properties")

    def get_properties(self, instance, fields):
        props = super().get_properties(instance, fields)
        raw = props.get("properties", {})
        selected_fields = self.context.get("selected_fields")
        if selected_fields:
            return {k: v for k, v in raw.items() if k in selected_fields}
        return raw