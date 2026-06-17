import math
import unicodedata

from django.contrib.gis.db.models.aggregates import Extent
from django.db.models import Avg, Case, Count, FloatField, IntegerField, Max, Min, Value, When, StdDev
from django.db.models.aggregates import Aggregate
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from geostore.models import Feature
from geostore.views import FeatureViewSet as GeostoreFeatureViewSet
from geostore.views.mixins import MultipleFieldLookupMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from project.terra_layer.style.utils import discretize

from .filters import (
    BBoxFilterBackend,
    NoAccentFilterBackend,
    OperatorFilterBackend,
    OrderingFilterBackend,
    PropertiesFilterBackend,
    SearchAllFieldsBackend,
    Unaccent,
    _clean_params,
)
from .mixins import AutoOrderMixin, PrefixBoostMixin
from .pagination import FeaturePagination
from .serializers import FeatureGeoSerializer, FeatureListSerializer

from .filters import CONTROL_PARAMS


class Median(Aggregate): # pas de median en django?? pas trouvé 
    function = 'PERCENTILE_CONT'
    name = 'median'
    output_field = FloatField()
    template = "%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)"

class FeatureViewSet(MultipleFieldLookupMixin, # recherche par ok ou identifir via geostore
                     PrefixBoostMixin, # tri avec boost prefix (commence par ...)
                     AutoOrderMixin, # ordre auto
                     GeostoreFeatureViewSet, # CRUD hérité de geostore
                     ):
    serializer_class = FeatureGeoSerializer # par défaut avec geom
    pagination_class = FeaturePagination # pagination perso
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_fields = ("pk", "identifier") # recherche par id numérique (pk) ou par identifier
    filter_backends = [
        SearchAllFieldsBackend,  # chercher partout
        PropertiesFilterBackend, # ?properties__code=valeur
        NoAccentFilterBackend,   # ?nom=éèàù... insensible aux accents
        OperatorFilterBackend,   # ?population>=100, opérateurs
        BBoxFilterBackend,       # ?bbox=w,x,y,z filtre par bbox
        OrderingFilterBackend,   # ?ordering=filed tri par champ
    ]
    ordering = "id" # par défaut id croissant

    def get_serializer_class(self):
        # ?geometry et ?all : backward compat, ne changent PAS le renderer
        if "geometry" in self.request.query_params or "all" in self.request.query_params:
            return FeatureGeoSerializer
        # .geojson ou ?format=geojson (change le renderer → pas de browseable API)
        if self.kwargs.get("format", "json") == "geojson":
            return FeatureGeoSerializer
        return FeatureListSerializer

    def get_serializer_context(self):
        # si recherce selon un ou des champs
        # on retourne que ces champs pour alléger
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
        # ajout de search_match dans les props
        # pour indiquer quel champ match la recherche
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
        # applique TOUS les filtres (search, bbox, op,...)
        queryset = self.filter_queryset(self.get_queryset())
        # paramètre ?search=valeur 
        search_param = self.request.query_params.get("search", "").strip()
        if search_param:
            # on ajoute les annoatations de boost
            queryset, search_boost_parts = self._add_search_boost_annotations(queryset, search_param)
        else:
            search_boost_parts = []

        # combine boost + auto order
        extra = search_boost_parts + self._collect_auto_order_parts()
        
        # applique le tri avec boost prefix puis auto order
        queryset = self._apply_prefix_boost(queryset, extra_order_parts=extra)
        
        # on pagine
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self._format_feature_response(serializer.data, search_param)
            return self.get_paginated_response(data)
        
        # pas de pagnation on retourne tout
        serializer = self.get_serializer(queryset, many=True)
        data = self._format_feature_response(serializer.data, search_param)
        return Response(data)

    @action(detail=False, methods=["get"])
    def count(self, request, layer=None):
        # retourne juste le nombre de résultats pour les filtres appliqués
        return Response({"count": self.filter_queryset(self.get_queryset()).count()})

    @action(detail=False, methods=["get"], url_path="stats/(?P<field>[^/.]+)")
    def stats(self, request, layer=None, field=None):
        qs = Feature.objects.filter(layer=self.get_layer())
        stats = qs.aggregate(
            min=Min(Cast(KeyTextTransform(field, "properties"), FloatField())),
            max=Max(Cast(KeyTextTransform(field, "properties"), FloatField())),
            avg=Avg(Cast(KeyTextTransform(field, "properties"), FloatField())),
            median=Median(Cast(KeyTextTransform(field, "properties"), FloatField())),
            std_dev=StdDev(Cast(KeyTextTransform(field, "properties"), FloatField())),
            count=Count("*"),
        )
        for k in ("min", "max", "avg", "median", "std_dev"):
            if stats.get(k) is not None:
                try:
                    stats[k] = round(float(stats[k]), 2) # on arrdondi à 2, à déterminer si interessant
                except (ValueError, TypeError):
                    pass
        return Response(stats)

    def _get_distinct_values_queryset(self, layer, field, q=""):
        # retourne les valeurs distinctes d'un champ
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
        # retourne la bbox des elements filtrés
        identifiers = request.query_params.get("identifier", "")
        identifiers = [i.strip() for i in identifiers.split(",") if i.strip()]

        qs = self.get_queryset()
        if identifiers:
            qs = qs.filter(identifier__in=identifiers)

        extent = qs.aggregate(Extent("geom"))["geom__extent"]
        if extent is None:
            return Response({"error": "Aucune donnée"}, status=404)
        return Response({"bbox": list(extent)})
    
    