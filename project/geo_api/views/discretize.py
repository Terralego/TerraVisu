from django.db.models import Case, Count, FloatField, IntegerField, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from geostore.models import Feature
from rest_framework.decorators import action
from rest_framework.response import Response

from project.terra_layer.style.utils import discretize as _discretize

from .stats import Quantile, _aggregate_stats


class DiscretizeMixin:
    @action(detail=False, methods=["get"],
            url_path="discretize/(?P<field>[^/.]+)")
    def discretize(self, request, layer=None, field=None):

        layer_obj = self.get_layer()
        method = request.query_params.get("method", "jenks")
        classes = int(request.query_params.get("classes", 5))

        breaks = _discretize(layer_obj, field, method, classes) or []

        qs = Feature.objects.filter(layer=layer_obj)
        cast_field = Cast(KeyTextTransform(field, "properties"), FloatField())
        entities_by_class = []
        if breaks and len(breaks) >= 2:
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
                 .values_list('klass', 'cnt')) # bug si class et count car réservé
            )
            entities_by_class = [class_counts.get(i, 0) for i in range(len(breaks) - 1)]

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
