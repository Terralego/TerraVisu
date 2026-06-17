import operator
import re
from functools import reduce

from django.contrib.gis.geos import Polygon
from django.db.models import F, FloatField, Func, Q, Value
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, NullIf
from geostore.filters import JSONSearchField
from rest_framework.filters import BaseFilterBackend, OrderingFilter


class Unaccent(Func):
    function = "unaccent"


class RegexpReplace(Func):
    function = "REGEXP_REPLACE"
    arity = 3 # prend 3 params, le texte, le pattern et le remplacement


## Paramètres de l'URL qui ne sont pas des filtres
CONTROL_PARAMS = {"limit", "offset", "ordering", "format", "fields", "search",
                  "bbox", "all", "geometry"}

## regex pour opérateurs
_RE_OPERATOR = re.compile(r"^(>=|<=|>|<)(.+)$")

## regex pour intervalles
_RE_RANGE = re.compile(r"^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$")


def _classify_params(query_params):
    # classe les params en types pour faciliter les filtres
    for key, value in _clean_params(query_params):
        if not value or key in CONTROL_PARAMS:
            yield "skip", None, None
            continue

        if key.startswith("properties__"):
            yield "skip", None, None
            continue

        if "," in value:
            items = [v.strip() for v in value.split(",") if v.strip()]
            yield "in", key, items
            continue

        m = _RE_OPERATOR.match(value)
        if m:
            yield "op", key, m.group(1), m.group(2).strip()
            continue

        m = _RE_RANGE.match(value)
        if m:
            yield "range", key, float(m.group(1)), float(m.group(2))
            continue

        yield "text", key, value


def _clean_params(query_params):
    # gère les >= > < <= dans l'url pour que <=X devienne inférieur ou égal à X
    for key, value in query_params.items():
        if not value:
            for op in (">=", "<=", ">", "<"):
                if op in key:
                    k, v = key.split(op, 1)
                    if v:
                        yield k, op + v
                        break
            else:
                yield key, value
        elif key[-1:] in ("<", ">"):
            yield key[:-1], key[-1] + "=" + value
        else:
            yield key, value


class SearchAllFieldsBackend(JSONSearchField):
    #récupère les champs à chercher
    def get_search_fields(self, view, request):
        # règle bug geostore bug quand pas de schema défini 
        fields = super().get_search_fields(view, request)
        if not fields:
            layer = view.get_layer()
            first = layer.features.values("properties").first()
            if first:
                fields = [f"properties__{k}" for k in first["properties"] if k]
        return fields

    # cherche dasn tous les champs
    def filter_queryset(self, request, queryset, view):
        # équivalent de search dans tous les champs, insensible aux accents
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)
        if not search_terms or not search_fields:
            return queryset
        filters = []
        for i, field in enumerate(search_fields):
            if field.startswith("properties__"):
                key = field[len("properties__"):]
                ann = f"_unas_{i}"
                queryset = queryset.annotate(**{
                    ann: Unaccent(KeyTextTransform(key, "properties"))
                })
            else:
                ann = f"_unas_{i}"
                queryset = queryset.annotate(**{
                    ann: Unaccent(F(field))
                })
            filters.append(Q(**{f"{ann}__icontains": Unaccent(Value(search_terms[0]))}))
        return queryset.filter(reduce(operator.or_, filters))


class NoAccentFilterBackend(BaseFilterBackend):
    """?nom=riège → icontains insensible aux accents sur properties->nom"""

    def filter_queryset(self, request, queryset, view):
        for cat, key, *rest in _classify_params(request.query_params):
            if cat != "text": # pas la peine de unaccent si pas du texte
                continue
            ann = f"_una_{key}"
            queryset = queryset.annotate(**{
                ann: Unaccent(KeyTextTransform(key, "properties"))
            }).filter(**{f"{ann}__icontains": Unaccent(Value(rest[0]))})
        return queryset


class PropertiesFilterBackend(BaseFilterBackend):
    # Remplace le JSONFieldFilterBackend de geostore qui buguait avec les nombres
    # Convertit les valeurs en int/float pour éviter la comparaison string vs jsonb
    """?properties__population__gte=100000 → filtre Django ORM sur le JSON"""

    def filter_queryset(self, request, queryset, view):
        for key, value in request.query_params.items():
            if not key.startswith("properties__") or not value:
                continue
            try:
                value = float(value) if "." in value else int(value)
            except (ValueError, TypeError):
                pass
            queryset = queryset.filter(**{key: value})
        return queryset


class OperatorFilterBackend(BaseFilterBackend):
    """?population>=1000, ?population=1000-5000, ?id_occ=OCC-09,OCC-11"""

    def filter_queryset(self, request, queryset, view):
        for cat, key, *rest in _classify_params(request.query_params):
            if cat == "in":
                queryset = queryset.filter(Q(**{f"properties__{key}__in": rest[0]}))
            elif cat in ("op", "range"):
                ann = f"_op_{key}"
                qs = queryset.annotate(**{ann: self._cast_numeric(key)})
                if cat == "op":
                    try:
                        op_val = float(rest[1])
                    except ValueError:
                        continue
                    op_map = {">=": "gte", ">": "gt", "<=": "lte", "<": "lt"}
                    queryset = qs.filter(**{f"{ann}__{op_map[rest[0]]}": op_val})
                else:
                    lo, hi = rest
                    queryset = qs.filter(**{f"{ann}__gte": lo, f"{ann}__lte": hi})
        return queryset

    @staticmethod
    def _cast_numeric(key):
        return Cast(NullIf(RegexpReplace(KeyTextTransform(key, "properties"), Value(r"[^\d.\-]"), Value("")), Value("")), FloatField())


class BBoxFilterBackend(BaseFilterBackend): # pour le moment pas utile
    """?bbox=min_lng,min_lat,max_lng,max_lat"""

    def filter_queryset(self, request, queryset, view):
        bbox = request.query_params.get("bbox")
        if not bbox:
            return queryset
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) != 4:
            return queryset
        polygon = Polygon.from_bbox(tuple(parts))
        return queryset.filter(geom__intersects=polygon)


class OrderingFilterBackend(OrderingFilter):
    """?ordering=-population → préfixe properties__ si pas champ modèle"""

    def get_valid_fields(self, queryset, view, context={}):
        fields = list(super().get_valid_fields(queryset, view, context=context))
        layer = view.get_layer() if hasattr(view, 'get_layer') else None
        if layer and layer.schema:
            fields += [(f'properties__{p}', layer.get_property_title(p))
                       for p in layer.layer_properties]
        return fields

    def remove_invalid_fields(self, queryset, fields, view, request):
        valid = {f[0] for f in self.get_valid_fields(queryset, view)}
        model_names = {f.name for f in queryset.model._meta.get_fields()}
        result = []
        for f in fields:
            stripped = f.lstrip('-')
            prefix = '-' if f.startswith('-') else ''
            if stripped in valid:
                result.append(f)
            elif stripped not in model_names:
                result.append(prefix + f'properties__{stripped}')
            else:
                result.append(f)
        return result
