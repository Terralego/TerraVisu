from django.db.models import Case, IntegerField, Value, When

from .filters import Unaccent, _classify_params


class AutoOrderMixin:
    def _collect_auto_order_parts(self):
        parts = []
        for cat, key, *rest in _classify_params(self.request.query_params):
            if cat == "skip":
                continue
            if cat == "op":
                ann = f"_op_{key}"
                parts.append(ann if rest[0] in (">", ">=") else f"-{ann}")
            elif cat == "range":
                parts.append(f"_op_{key}")
        return parts


class PrefixBoostMixin:
    def _apply_prefix_boost(self, queryset, extra_order_parts=None):
        if "ordering" in self.request.query_params:
            return queryset
        text_filters = [
            (key, rest[0])
            for cat, key, *rest in _classify_params(self.request.query_params)
            if cat == "text" and rest
        ]
        for key, value in text_filters:
            ann = f"_una_{key}"
            queryset = queryset.annotate(**{
                f"_boost_{key}": Case(
                    When(**{f"{ann}__istartswith": Unaccent(Value(value))}, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            })
        order_parts = [f"_boost_{key}" for key, _ in text_filters
                       ] + [f"_una_{key}" for key, _ in text_filters
                             ] + (extra_order_parts or [])
        if order_parts:
            return queryset.order_by(*order_parts)
        return queryset
