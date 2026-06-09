import json

from django.db import connection
from django.http import JsonResponse

BASE_LIMIT = 100
BASE_OFFSET = 0


def communes(request):
    try:
        limit = min(int(request.GET.get("limit", BASE_LIMIT)), 1000000)
    except (ValueError, TypeError):
        limit = BASE_LIMIT
    try:
        offset = int(request.GET.get("offset", BASE_OFFSET))
    except (ValueError, TypeError):
        offset = BASE_OFFSET

    nom = request.GET.get("nom", "")
    code = request.GET.get("code", "")
    order_by = request.GET.get("order_by", "")

    sql_select = """
        SELECT properties, ST_AsGeoJSON(geom)::json as geom_json
        FROM geostore_feature f
        JOIN geostore_layer l ON f.layer_id = l.id
    """
    where_sql = "WHERE l.name = %s"
    where_params = ["communes-simplifiees"]

    order_parts = []

    if nom:
        where_sql += " AND unaccent(properties->>'nom') ILIKE %s"
        where_params.append(f"%{nom}%")
        order_parts.append(
            "CASE WHEN unaccent(properties->>'nom') ILIKE %s THEN 0 ELSE 1 END"
        )
        where_params.append(f"{nom}%")

    if code:
        where_sql += " AND unaccent(properties->>'code') ILIKE %s"
        where_params.append(f"%{code}%")
        order_parts.append(
            "CASE WHEN unaccent(properties->>'code') ILIKE %s THEN 0 ELSE 1 END"
        )
        where_params.append(f"{code}%")

    if order_by:
        parts = order_by.split()
        field = parts[0]
        direction = parts[1].upper() if len(parts) > 1 else "ASC"
        if direction not in ("ASC", "DESC"):
            direction = "ASC"
        order_parts.append(f"unaccent(properties->>'{field}') {direction}")
    else:
        order_parts.append("f.id ASC")

    with connection.cursor() as cursor:
        data_sql = f"""
            {sql_select}
            {where_sql}
            ORDER BY {', '.join(order_parts)}
            LIMIT %s OFFSET %s
        """
        data_params = where_params + [limit, offset]
        cursor.execute(data_sql, data_params)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    features = []
    # for row in rows:
    #     props = row["properties"]
    #     if isinstance(props, str):
    #         props = json.loads(props)
    #     geom = row["geom_json"]
    #     if isinstance(geom, str):
    #         geom = json.loads(geom)
    #     features.append({"type": "Feature", "geometry": geom, "properties": props})

    return JsonResponse({
        "type": "FeatureCollection",
        "features": rows,
    })