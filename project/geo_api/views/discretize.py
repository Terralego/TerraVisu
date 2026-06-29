from django.db.models import Case, Count, FloatField, IntegerField, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from geostore.models import Feature
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from project.terra_layer.style.utils import discretize as _discretize

from .stats import _aggregate_stats


def _parse_manual_breaks(breaks_str):
    if not breaks_str or not breaks_str.strip():
        return None
    try:
        raw = [
            float(x.strip())
            for x in breaks_str.split(",")
            if x.strip()
        ]
    except (ValueError, TypeError):
        return None
    if len(raw) < 2:
        return None
    if not all(raw[i] < raw[i + 1] for i in range(len(raw) - 1)):
        return None
    return raw


def _compute_entities(qs, cast_field, breaks):
    if not breaks or len(breaks) < 2:
        return []
    cases = []
    last_idx = len(breaks) - 2
    for i in range(last_idx + 1):
        if i == last_idx:
            w = When(val__gte=Value(breaks[i], output_field=FloatField()),
                     val__lte=Value(breaks[i + 1], output_field=FloatField()),
                     then=Value(i))
        else:
            w = When(val__gte=Value(breaks[i], output_field=FloatField()),
                     val__lt=Value(breaks[i + 1], output_field=FloatField()),
                     then=Value(i))
        cases.append(w)
    class_counts = dict(
        (qs
         .annotate(val=cast_field)
         .annotate(klass=Case(*cases, output_field=IntegerField(), default=Value(-1)))
         .exclude(klass__lt=0)
         .values('klass')
         .annotate(cnt=Count('*'))
         .values_list('klass', 'cnt'))
    )
    return [class_counts.get(i, 0) for i in range(len(breaks) - 1)]


class DiscretizeMixin:
    @action(detail=False, methods=["get"],
            url_path="discretize/(?P<field>[^/.]+)")
    def discretize(self, request, layer=None, field=None):

        layer_obj = self.get_layer()
        method = request.query_params.get("method", "jenks")
        classes = int(request.query_params.get("classes", 5))

        qs = Feature.objects.filter(layer=layer_obj)
        cast_field = Cast(KeyTextTransform(field, "properties"), FloatField())

        if method == "manual":
            breaks_str = request.query_params.get("breaks", "")
            if not breaks_str.strip():
                return Response(
                    {"error": "breaks parameter is required for manual method"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            breaks = _parse_manual_breaks(breaks_str)
            if breaks is None or len(breaks) < 2:
                return Response(
                    {"error": "invalid breaks parameter"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            classes = len(breaks) - 1
            entities_by_class = _compute_entities(qs, cast_field, breaks)
            stats = _aggregate_stats(qs, cast_field)
            return Response({
                "breaks": breaks,
                "entitiesByClass": entities_by_class,
                "stats": stats,
            })

        breaks = _discretize(layer_obj, field, method, classes) or []
        entities_by_class = _compute_entities(qs, cast_field, breaks)

        stats = _aggregate_stats(qs, cast_field)

        if not breaks or len(breaks) < 2:
            breaks = [stats.get("min") or 0, stats.get("max") or 1]
            entities_by_class = []
            for i in range(len(breaks) - 1):
                cnt = qs.filter(
                    **{f"properties__{field}__gte": breaks[i]},
                    **{f"properties__{field}__lte": breaks[i + 1]},
                ).count()
                entities_by_class.append(cnt)

        while len(entities_by_class) < classes:
            entities_by_class.append(0)
            breaks.append(breaks[-1])

        return Response({
            "breaks": breaks,
            "entitiesByClass": entities_by_class,
            "stats": stats,
        })
