import django_filters
from django_filters.rest_framework import FilterSet

from project.terra_layer.models import Layer, Scene


class SceneFilterSet(FilterSet):
    def filter_user_scenes(self, queryset, name, value):
        if value:
            return Scene.objects.get_user_scenes(self.request.user)
        return queryset

    viewer = django_filters.BooleanFilter(
        help_text="Filter out scenes that are not visible to the viewer for frontend",
        method="filter_user_scenes",
    )

    class Meta:
        model = Scene
        fields = ["viewer"]


class LayerFilterSet(FilterSet):
    class Meta:
        model = Layer
        fields = [
            "source",
            "group",
            "group__view",
            "active_by_default",
            "in_tree",
            "table_enable",
        ]
