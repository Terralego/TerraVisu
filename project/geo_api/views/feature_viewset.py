import unicodedata

from django.db.models import Case, IntegerField, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.contrib.gis.db.models.aggregates import Extent
from geostore.models import Feature
from geostore.views import FeatureViewSet as GeostoreFeatureViewSet
from geostore.views.mixins import MultipleFieldLookupMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from ..filters import (
    BBoxFilterBackend,
    NoAccentFilterBackend,
    OperatorFilterBackend,
    OrderingFilterBackend,
    PropertiesFilterBackend,
    SearchAllFieldsBackend,
    Unaccent,
    _clean_params,
)
from ..filters import CONTROL_PARAMS
from ..mixins import AutoOrderMixin, PrefixBoostMixin
from ..pagination import FeaturePagination
from ..serializers import FeatureGeoSerializer, FeatureListSerializer

from .discretize import DiscretizeMixin
from .stats import StatsMixin


class FeatureViewSet(StatsMixin, DiscretizeMixin,
                     MultipleFieldLookupMixin,
                     PrefixBoostMixin,
                     AutoOrderMixin,
                     GeostoreFeatureViewSet):
    serializer_class = FeatureGeoSerializer
    pagination_class = FeaturePagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_fields = ("pk", "identifier")
    filter_backends = [
        SearchAllFieldsBackend,
        PropertiesFilterBackend,
        NoAccentFilterBackend,
        OperatorFilterBackend,
        BBoxFilterBackend,
        OrderingFilterBackend,
    ]
    ordering = "id"

    def get_serializer_class(self):
        if "geometry" in self.request.query_params or "all" in self.request.query_params:
            return FeatureGeoSerializer
        if self.kwargs.get("format", "json") == "geojson":
            return FeatureGeoSerializer
        return FeatureListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        requested_fields = self.request.query_params.get("fields", "")
        if requested_fields:
            context["selected_fields"] = [f.strip() for f in requested_fields.split(",") if f.strip()]
        elif "all" not in self.request.query_params and "geometry" not in self.request.query_params:
            filter_fields = [
                key for key, _ in _clean_params(self.request.query_params)
                if key not in CONTROL_PARAMS and not key.startswith("properties__")
            ]
            if filter_fields:
                context["selected_fields"] = filter_fields
        return context

    def _get_search_fields(self):
        layer = self.get_layer()
        if layer and layer.schema:
            return [f"properties__{prop}" for prop in layer.layer_properties]
        first = layer.features.values("properties").first() if layer else None
        if first:
            return [f"properties__{k}" for k in first["properties"] if k]
        return []

    def _add_search_boost_annotations(self, queryset, search_param):
        search_fields = self._get_search_fields()
        if not search_fields:
            return queryset, []
        order_parts = []
        for field in search_fields:
            key = field.split("__", 1)[-1]
            ann = f"_sboost_{key}"
            una_ann = f"_una_sboost_{key}"
            queryset = queryset.annotate(**{
                una_ann: Unaccent(KeyTextTransform(key, "properties")),
                ann: Case(
                    When(**{f"{una_ann}__istartswith": Unaccent(Value(search_param))}, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            })
            order_parts.append(ann)
        order_parts.extend(search_fields)
        return queryset, order_parts

    @staticmethod
    def _strip_accents(s):
        return "".join(
            c for c in unicodedata.normalize("NFKD", s)
            if not unicodedata.category(c).startswith("M")
        )

    def _inject_search_match(self, features, search_param):
        if not search_param:
            return
        search_clean = self._strip_accents(search_param.lower())
        for feature in features:
            props = feature.get("properties", {})
            for key, val in props.items():
                if val is not None and search_clean in self._strip_accents(str(val).lower()):
                    props["search_match"] = key
                    break

    def _is_geojson_format(self):
        if "geometry" in self.request.query_params or "all" in self.request.query_params:
            return True
        return self.kwargs.get("format", "json") == "geojson"

    def _format_feature_response(self, data, search_param):
        if isinstance(data, list):
            if self._is_geojson_format():
                data = {"type": "FeatureCollection", "features": data}
        if search_param:
            features = data if isinstance(data, list) else data.get("features", [])
            self._inject_search_match(features, search_param)
        return data

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        search_param = self.request.query_params.get("search", "").strip()
        if search_param:
            queryset, search_boost_parts = self._add_search_boost_annotations(queryset, search_param)
        else:
            search_boost_parts = []

        extra = search_boost_parts + self._collect_auto_order_parts()

        queryset = self._apply_prefix_boost(queryset, extra_order_parts=extra)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self._format_feature_response(serializer.data, search_param)
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = self._format_feature_response(serializer.data, search_param)
        return Response(data)

    def _get_distinct_values_queryset(self, layer, field, q=""):
        qs = Feature.objects.filter(layer=layer)
        lookup = f"properties__{field}"
        if q:
            ann = f"_una_{field}"
            qs = qs.annotate(**{
                ann: Unaccent(KeyTextTransform(field, "properties")),
                f"_boost_{field}": Case(
                    When(**{f"{ann}__istartswith": Unaccent(Value(q))}, then=Value(0)),
                    default=Value(1), output_field=IntegerField(),
                )
            }).filter(**{f"{ann}__icontains": Unaccent(Value(q))})
            return qs.values_list(lookup, flat=True).order_by(f"_boost_{field}", ann).distinct()
        return qs.values_list(lookup, flat=True).distinct().order_by(lookup)

    @action(detail=False, methods=["get"], url_path="distinct/(?P<field>[^/.]+)")
    def distinct(self, request, layer=None, field=None):
        q = request.query_params.get("q", "")
        qs = self._get_distinct_values_queryset(self.get_layer(), field, q)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(list(qs))

    @action(detail=False, methods=["get"], url_path="distinct/all/(?P<field>[^/.]+)")
    def distinct_all(self, request, layer=None, field=None):
        q = request.query_params.get("q", "")
        qs = self._get_distinct_values_queryset(self.get_layer(), field, q)
        return Response(list(qs))

    @action(detail=False, methods=["get"])
    def extent(self, request, layer=None):
        identifiers = request.query_params.get("identifier", "")
        identifiers = [i.strip() for i in identifiers.split(",") if i.strip()]

        qs = self.get_queryset()
        if identifiers:
            qs = qs.filter(identifier__in=identifiers)

        extent = qs.aggregate(Extent("geom"))["geom__extent"]
        if extent is None:
            return Response({"error": "Aucune donnée"}, status=404)
        return Response({"bbox": list(extent)})

    @action(detail=False, methods=["get"])
    def count(self, request, layer=None):
        return Response({"count": self.filter_queryset(self.get_queryset()).count()})
