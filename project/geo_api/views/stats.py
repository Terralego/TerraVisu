import math

from django.db.models import Avg, Case, Count, FloatField, IntegerField, Max, Min, StdDev, Value, When
from django.db.models.aggregates import Aggregate
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, Random
from geostore.models import Feature
from rest_framework.decorators import action
from rest_framework.response import Response


class Quantile(Aggregate):
    function = 'PERCENTILE_CONT'
    output_field = FloatField()
    template = "%(function)s(%(quantile)s) WITHIN GROUP (ORDER BY %(expressions)s)"


def _count_by_intervals(qs, cast_field, intervals):
    """
    intervals: list of (x0, x1) tuples
    Returns list of counts, one per interval.
    All intervals use val__gte x0 + val__lt x1, except the last which uses val__lte x1.
    """
    if not intervals:
        return []
    cases = []
    last_idx = len(intervals) - 1
    for i, (x0, x1) in enumerate(intervals):
        if i == last_idx:
            w = When(val__gte=Value(x0, output_field=FloatField()),
                     val__lte=Value(x1, output_field=FloatField()),
                     then=Value(i))
        else:
            w = When(val__gte=Value(x0, output_field=FloatField()),
                     val__lt=Value(x1, output_field=FloatField()),
                     then=Value(i))
        cases.append(w)
    bucket_counts = dict(
        (qs
         .annotate(val=cast_field)
         .annotate(bucket=Case(*cases, output_field=IntegerField(), default=Value(-1)))
         .exclude(bucket__lt=0)
         .values('bucket')
         .annotate(cnt=Count('*'))
         .values_list('bucket', 'cnt'))
    )
    return [bucket_counts.get(i, 0) for i in range(len(intervals))]


def _round_val(val, precision=2):
    if val is not None:
        try:
            return round(float(val), precision)
        except (ValueError, TypeError):
            pass
    return val


def _aggregate_stats(qs, cast_field):
    stats = qs.aggregate(
        min=Min(cast_field),
        max=Max(cast_field),
        avg=Avg(cast_field),
        median=Quantile(cast_field, quantile=0.50),
        std_dev=StdDev(cast_field),
        count=Count(cast_field),
        q1=Quantile(cast_field, quantile=0.25),
        q3=Quantile(cast_field, quantile=0.75),
        total_count=Count("*"),
    )
    for k in ("min", "max", "avg", "median", "std_dev", "q1", "q3"):
        stats[k] = _round_val(stats.get(k))
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

    intervals = []
    for i in range(nb_bins):
        x0 = min_val + i * bin_width
        x1 = (min_val + (i + 1) * bin_width) if i < nb_bins - 1 else (max_val + 0.0001)
        intervals.append((x0, x1))

    bucket_counts = _count_by_intervals(values_qs, cast_field, intervals)

    bins = []
    for i in range(nb_bins):
        x0 = min_val + i * bin_width
        x1 = (min_val + (i + 1) * bin_width) if i < nb_bins - 1 else (max_val + 0.0001)
        bins.append({
            "x0": _round_val(x0),
            "x1": _round_val(x1),
            "count": bucket_counts[i],
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

        stats = _aggregate_stats(qs, cast_field)

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
            count=stats.get("count"),
        )

        boxplot = {
            "min": _round_val(min_val),
            "q1": _round_val(q1_val),
            "median": _round_val(stats.get("median")),
            "q3": _round_val(q3_val),
            "max": _round_val(max_val),
        }

        lookup = f"properties__{field}"
        qs_filtered = qs.filter(**{f"{lookup}__isnull": False}).exclude(**{lookup: ""})
        sample_count = stats.get("count", 0)
        if sample_count > 1000:
            qs_sample = qs_filtered.annotate(_rnd=Random()).filter(
                _rnd__lt=1000.0 / sample_count
            ).values_list(lookup, flat=True)[:1000]
        else:
            qs_sample = qs_filtered.values_list(lookup, flat=True)
        sample = [float(v) for v in qs_sample if v is not None]

        return Response({"bins": bins, "boxplot": boxplot, "sample": sample})
