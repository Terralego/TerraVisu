import kmeans1d
from django.db import connection


def _fetch_values(geo_layer, field):
    """Retourne list[float] triée des valeurs non-nulles du champ `field` pour le layer."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT (properties->>%(field)s)::numeric
            FROM geostore_feature
            WHERE layer_id = %(layer_id)s
              AND (properties->>%(field)s)::numeric IS NOT NULL
            ORDER BY 1
            """,
            {"field": field, "layer_id": geo_layer.id},
        )
        return [float(row[0]) for row in cursor]


def discretize_jenks_kmeans1d(geo_layer, field, class_count):
    """K-means 1D (C) : approximation Jenks, rapide, non déterministe.  list[float] de class_count+1 bornes."""
    values = _fetch_values(geo_layer, field)
    if len(values) < 2:
        return []
    _, centroids = kmeans1d.cluster(values, class_count)
    sorted_c = sorted(centroids)
    breaks = [min(values)]
    for i in range(len(sorted_c) - 1):
        breaks.append((sorted_c[i] + sorted_c[i + 1]) / 2)
    breaks.append(max(values))
    return breaks


