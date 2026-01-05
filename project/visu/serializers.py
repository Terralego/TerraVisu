from rest_framework import serializers

from project.visu.models import ExtraMenuItem


class ExtraMenuItemSerializer(serializers.ModelSerializer):
    id = serializers.SlugField()

    class Meta:
        model = ExtraMenuItem
        fields = ("id", "label", "href", "icon")
