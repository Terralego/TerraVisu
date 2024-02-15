from django.db.models import Func, IntegerField
from django_filters import rest_framework as filters

from .models import Source


class SourceOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if value and any(v in ["status", "-status"] for v in value):
            # as status display in admin differ along with report__status, source type or number of errors
            # we should take in consideration
            qs = qs.annotate(
                num_errors=Func(
                    "report__errors",
                    function="jsonb_array_length",
                    output_field=IntegerField(),
                )
            )
            if "-status" in value:
                orders = [
                    "-status",
                    "-report__status",
                    "-polymorphic_ctype__model",
                    "-num_errors",
                ]

            else:
                orders = [
                    "status",
                    "report__status",
                    "polymorphic_ctype__model",
                    "-num_errors",
                ]

            qs = qs.order_by(*orders)
            return qs
        return super().filter(qs, value)


class SourceFilterSet(filters.FilterSet):
    q = filters.CharFilter(field_name="name", lookup_expr="icontains")
    status = filters.ChoiceFilter(choices=Source.Status.choices, method="filter_status")
    ordering = SourceOrderingFilter(
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

    def filter_status(self, queryset, name, value):
        if value is not None and value != "":

            # WMTS sources should be excluded from status filter
            return queryset.filter(status=int(value)).exclude(
                polymorphic_ctype__model__icontains="wmts"
            )
        return queryset

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
