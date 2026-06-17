from django.db.models import Case, When, IntegerField, Value

from .filters import Unaccent, _classify_params


class AutoOrderMixin:
    # ajout auto ORDER BY sur les filtres utilisés
    def _collect_auto_order_parts(self):
        parts = []
        for cat, key, *rest in _classify_params(self.request.query_params):
            if cat == "skip": # params internes donc ignorés
                continue
            if cat == "op": # opérateurs
                ann = f"_op_{key}"
                parts.append(ann if rest[0] in (">", ">=") else f"-{ann}")
            elif cat == "range": # intervalles
                parts.append(f"_op_{key}")
        return parts


class PrefixBoostMixin:
    # boost les résultats qui commencent par la requête
    def _apply_prefix_boost(self, queryset, extra_order_parts=None):
        if "ordering" in self.request.query_params: # on skip si ordering spécifié
            return queryset
        text_filters = [
            (key, rest[0])
            for cat, key, *rest in _classify_params(self.request.query_params)
            if cat == "text" and rest
        ]
        for key, value in text_filters:
            ann = f"_una_{key}" # nom de l'annotation : _una_fieldname
            queryset = queryset.annotate(**{
                f"_boost_{key}": Case(
                    When(**{f"{ann}__istartswith": Unaccent(Value(value))}, then=Value(0)), # SI commence par le terme ALORS 0
                    default=Value(1), # SINON 1
                    output_field=IntegerField(), # les 0 remonte plus haut que les 1
                )
            })

        # CONSTRUCTION du ORDER BY
        # d'abord les boosts puis les valeurs elles-mêmes puis les contient
        order_parts = [f"_boost_{key}" for key, _ in text_filters
                       ] + [f"_una_{key}" for key, _ in text_filters
                             ] + (extra_order_parts or [])
        if order_parts:
            return queryset.order_by(*order_parts)
        return queryset
