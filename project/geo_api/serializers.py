from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from geostore.models import Feature
from geostore.serializers import FeatureSerializer as GeostoreFeatureSerializer


class FeatureListSerializer(GeostoreFeatureSerializer):
    """
    Serializer sans geometry pour réponse plus légère
    Réutilise le FeatureSerializer de geostore (validateurs, champs)
    mais restreint aux champs utiles sans geom
    """
    class Meta(GeostoreFeatureSerializer.Meta):
        fields = ("id", "identifier", "properties")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # filtre si champs spécifiques
        selected_fields = self.context.get("selected_fields")
        if selected_fields and isinstance(data.get("properties"), dict):
            data["properties"] = {
                k: v for k, v in data["properties"].items() if k in selected_fields
            }
        return data


class FeatureGeoSerializer(GeoFeatureModelSerializer):
    """
    Serializer avec geometry (GeoJSON)
    --> hérite de GeoFeatureModelSerializer
    """
    class Meta:
        model = Feature
        geo_field = "geom" # champ de géométrie PostGIS
        fields = ("id", "identifier", "properties")

    def get_properties(self, instance, fields):
        props = super().get_properties(instance, fields)
        raw = props.get("properties", {})
        selected_fields = self.context.get("selected_fields")
        if selected_fields:
            return {k: v for k, v in raw.items() if k in selected_fields}
        return raw