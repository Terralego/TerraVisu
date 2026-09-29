import kmeans1d
import numpy as np
from django.db import connection

# Nettoie les séparateurs puis vérifie que la valeur est bien numérique : une
# propriété non numérique donne NULL au lieu de faire échouer toute la requête.
_NUMERIC_SQL = """
    substring(regexp_replace(properties->>%(field)s, '[^0-9.-]', '', 'g')
              from '^-?[0-9]+(?:\\.[0-9]+)?$')::double precision
"""


def _fetch_values(geo_layer, field):
    """Retourne un ndarray trié des valeurs numériques du champ `field` du layer.

    numpy plutôt qu'une liste Python : 8 octets par valeur au lieu d'environ 32,
    pour un résultat identique au bit près en sortie de kmeans1d.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {_NUMERIC_SQL} AS value
            FROM geostore_feature
            WHERE layer_id = %(layer_id)s
              AND {_NUMERIC_SQL} IS NOT NULL
            ORDER BY 1
            """,
            {"field": field, "layer_id": geo_layer.id},
        )
        return np.fromiter((row[0] for row in cursor), dtype=np.float64)


def discretize_jenks_kmeans1d(geo_layer, field, class_count):
    """K-means 1D (C) : approximation Jenks, rapide. list[float] de class_count+1 bornes."""
    values = _fetch_values(geo_layer, field)
    if len(values) < 2:
        return []
    _, centroids = kmeans1d.cluster(values, class_count)
    sorted_c = sorted(centroids)
    breaks = [float(values.min())]
    for i in range(len(sorted_c) - 1):
        breaks.append((sorted_c[i] + sorted_c[i + 1]) / 2)
    breaks.append(float(values.max()))
    return breaks
