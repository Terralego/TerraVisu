from django_filters import rest_framework as filters

from .models import Source


class SourceFilterSet(filters.FilterSet):
    q = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Source
        fields = (
            "polymorphic_ctype",
            "polymorphic_ctype__model",
            "geom_type",
            "q",
            "status",
        )
