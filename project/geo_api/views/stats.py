import math

from django.db.models import Avg, Case, Count, FloatField, IntegerField, Max, Min, StdDev, Value, When
from django.db.models.aggregates import Aggregate
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from geostore.models import Feature
from rest_framework.decorators import action
from rest_framework.response import Response


class Quantile(Aggregate):
    function = 'PERCENTILE_CONT'
    output_field = FloatField()
    template = "%(function)s(%(quantile)s) WITHIN GROUP (ORDER BY %(expressions)s)"


def _aggregate_stats(qs, cast_field):
    stats = qs.aggregate(
        min=Min(cast_field),
        max=Max(cast_field),
        avg=Avg(cast_field),
        median=Quantile(cast_field, quantile=0.50),
        std_dev=StdDev(cast_field),
        count=Count("*"),
    )
    for k in ("min", "max", "avg", "median", "std_dev"):
        if stats.get(k) is not None:
            try:
                stats[k] = round(float(stats[k]), 2)
            except (ValueError, TypeError):
                pass
    return stats


def _compute_fd_bins(values_qs, field, min_val, max_val, q1, q3, count=None):
    if count is None:
        count = values_qs.count()

    if count < 2 or min_val == max_val:
        return [{"x0": float(min_val), "x1": float(max_val), "count": count}]

    iqr = q3 - q1
    if iqr == 0:
        bin_width = (max_val - min_val) / 10
    else:
        bin_width = 2 * iqr / (count ** (1 / 3))

    if bin_width <= 0:
        bin_width = (max_val - min_val) / 10

    nb_bins = max(1, math.ceil((max_val - min_val) / bin_width))
    nb_bins = min(nb_bins, 100)

    cast_field = Cast(KeyTextTransform(field, "properties"), FloatField())

    cases = []
    for i in range(nb_bins):
        x0 = min_val + i * bin_width
        x1 = (min_val + (i + 1) * bin_width) if i < nb_bins - 1 else (max_val + 0.0001)
        cases.append(
            When(val__gte=Value(x0, output_field=FloatField()),
                 val__lt=Value(x1, output_field=FloatField()),
                 then=Value(i))
        )

    bucket_counts = dict(
        (values_qs
         .annotate(val=cast_field)
         .annotate(bucket=Case(*cases, output_field=IntegerField(), default=Value(-1)))
         .exclude(bucket__lt=0)
         .values('bucket')
         .annotate(cnt=Count('*'))
         .values_list('bucket', 'cnt'))
    )

    bins = []
    for i in range(nb_bins):
        x0 = min_val + i * bin_width
        x1 = (min_val + (i + 1) * bin_width) if i < nb_bins - 1 else (max_val + 0.0001)
        bins.append({
            "x0": round(x0, 2),
            "x1": round(x1, 2),
            "count": bucket_counts.get(i, 0),
        })

    return bins


class StatsMixin:
    @action(detail=False, methods=["get"], url_path="stats/(?P<field>[^/.]+)")
    def stats(self, request, layer=None, field=None):
        qs = Feature.objects.filter(layer=self.get_layer())
        cast_field = Cast(KeyTextTransform(field, "properties"), FloatField())
        stats = _aggregate_stats(qs, cast_field)
        return Response(stats)

    @action(detail=False, methods=["get"],
            url_path="stats/(?P<field>[^/.]+)/distribution")
    def distribution(self, request, layer=None, field=None):
        cast_field = Cast(KeyTextTransform(field, "properties"), FloatField())
        qs = Feature.objects.filter(layer=self.get_layer())

        stats = qs.aggregate(
            min=Min(cast_field),
            max=Max(cast_field),
            q1=Quantile(cast_field, quantile=0.25),
            median=Quantile(cast_field, quantile=0.50),
            q3=Quantile(cast_field, quantile=0.75),
            total_count=Count("*"),
        )

        min_val = stats.get("min")
        max_val = stats.get("max")
        if min_val is None or max_val is None:
            return Response({"bins": [], "boxplot": {}, "sample": []})

        q1_val = stats.get("q1")
        q3_val = stats.get("q3")

        bins = _compute_fd_bins(
            qs, field,
            float(min_val), float(max_val),
            float(q1_val or 0), float(q3_val or 0),
            count=stats.get("total_count"),
        )

        boxplot = {
            "min": round(float(min_val), 2),
            "q1": round(float(q1_val), 2) if q1_val else None,
            "median": round(float(stats["median"]), 2) if stats.get("median") else None,
            "q3": round(float(q3_val), 2) if q3_val else None,
            "max": round(float(max_val), 2),
        }

        lookup = f"properties__{field}"
        sample = list(
            qs.filter(**{f"{lookup}__isnull": False})
            .exclude(**{lookup: ""})
            .values_list(lookup, flat=True)
            .order_by("?")[:1000]
        )
        sample = [float(v) for v in sample if v is not None]

        for key in ("min", "max", "q1", "median", "q3"):
            if boxplot.get(key) is not None:
                try:
                    boxplot[key] = round(float(boxplot[key]), 2)
                except (ValueError, TypeError):
                    pass

        return Response({"bins": bins, "boxplot": boxplot, "sample": sample})
