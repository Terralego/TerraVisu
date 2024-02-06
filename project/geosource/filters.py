from django_filters import rest_framework as filters

from .models import Source


class SourceFilterSet(filters.FilterSet):
    q = filters.CharFilter(field_name="name", lookup_expr="icontains")
    ordering = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("polymorphic_ctype__model", "source_type"),
            ("geom_type", "geom_type"),
            ("id", "id"),
            ("slug", "slug"),
            ("status", "status"),
            ("updated_at", "updated_at"),
            ("layers_count", "layers"),
        )
    )

    class Meta:
        model = Source
        fields = (
            "polymorphic_ctype",
            "polymorphic_ctype__model",
            "report__status",
            "geom_type",
            "q",
            "status",
            "ordering",
        )
