import math
import numbers
from functools import reduce

from django.db import connection

style_type_2_legend_shape = {
    "fill-extrusion": "square",
    "fill": "square",
    "circle": "circle",
    "symbol": "symbol",
    "line": "line",
    "piechart": "circle",
}

stroke_color_props = ["line_color", "stroke_color", "outline_color"]
stroke_width_props = ["line_width", "stroke_width"]
shape_size_props = ["size", "radius"]


def style_type_2_legend_property(style_type):
    if any([s in style_type for s in stroke_color_props]):
        return "strokeColor"
    if any([s in style_type for s in stroke_width_props]):
        return "strokeWidth"
    if any([s in style_type for s in shape_size_props]):
        return "size"
    return "color"


def _flatten(levels):
    """
    Flatten 2-level array.
    [[1,2], [3, 4, 5]] -> [1, 2, 3, 4, 5]
    """
    return list(reduce(lambda x, y: x + y, levels or []))


def get_min_max(geo_layer, field):
    """
    Return the max and the min value of a property.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                bool_or((properties->>%(field)s)::numeric IS NULL) AS is_null,
                min((properties->>%(field)s)::numeric) AS min,
                max((properties->>%(field)s)::numeric) AS max
            FROM
                geostore_feature
            WHERE
                layer_id = %(layer_id)s
            """,
            {"field": field, "layer_id": geo_layer.id},
        )
        row = cursor.fetchone()
        is_null, min, max = row
        return [is_null == True, min, max]  # noqa


def get_positive_min_max(geo_layer, field):
    """
    Return the max and the min value of a property.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                bool_or((properties->>%(field)s)::numeric IS NULL) AS is_null,
                min((properties->>%(field)s)::numeric) AS min,
                max((properties->>%(field)s)::numeric) AS max
            FROM
                geostore_feature
            WHERE
                layer_id = %(layer_id)s AND
                (properties->>%(field)s)::numeric > 0
            """,
            {"field": field, "layer_id": geo_layer.id},
        )
        row = cursor.fetchone()
        is_null, min, max = row
        return [is_null == True, min, max]  # noqa


def discretize_quantile(geo_layer, field, class_count):
    """
    Compute Quantile class boundaries from a layer property.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH
            ntiles AS (
                SELECT
                    (properties->>%(field)s)::numeric AS value,
                    ntile(%(class_count)s) OVER (ORDER BY (properties->>%(field)s)::numeric) AS ntile
                FROM
                    geostore_feature
                WHERE
                    layer_id = %(layer_id)s
                UNION ALL
                SELECT
                    NULL AS value,
                    NULL AS ntile
                FROM
                    geostore_feature
                WHERE
                    layer_id = %(layer_id)s AND
                    (properties->>%(field)s)::numeric IS NOT NULL
            )
            SELECT
                min(value) AS boundary,
                max(value) AS max
            FROM
                ntiles
            GROUP BY
                ntile
            ORDER BY
                ntile
            """,
            {"field": field, "class_count": class_count, "layer_id": geo_layer.id},
        )
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            rows = [row for row in rows if row[0] is not None]
            if len(rows) == 0:
                return []
            else:
                # Each class start + last class end
                return [r[0] for r in rows] + [rows[-1][1]]


def discretize_jenks(geo_layer, field, class_count):
    """
    Compute Jenks class boundaries from a layer property.
    Note: Use PostGIS ST_ClusterKMeans() as k-means function.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH
            kmeans AS (
                SELECT
                    (properties->>%(field)s)::numeric AS field,
                    ST_ClusterKMeans(
                        ST_MakePoint((properties->>%(field)s)::numeric, 0),
                        least(%(class_count)s, (SELECT count(*) FROM geostore_feature WHERE layer_id = %(layer_id)s))::integer
                    ) OVER () AS class_id
                FROM
                    geostore_feature
                WHERE
                    layer_id = %(layer_id)s
            )
            SELECT
                min(field) AS min,
                max(field) AS max
            FROM
                kmeans
            GROUP BY
                class_id
            ORDER BY
                min,
                max
            """,
            {"field": field, "class_count": class_count, "layer_id": geo_layer.id},
        )
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            rows = [row for row in rows if row[0] is not None]
            if len(rows) == 0:
                return []
            else:
                # Each class start + last class end
                return [r[0] for r in rows] + [rows[-1][1]]


def discretize_equal_interval(geo_layer, field, class_count):
    """
    Compute QuantiEqual Interval class boundaries from a layer property.
    """
    is_null, min, max = get_min_max(geo_layer, field)
    if min is not None and max is not None and isinstance(min, numbers.Number):
        delta = (max - min) / class_count
        return [min + delta * i for i in range(0, class_count + 1)]
    else:
        return None


def discretize(geo_layer, field, method, class_count):
    """
    Select a method to compute class boundaries.
    Compute (len(class_count) + 1) boundaries.
    Note, can returns less boundaries than requested if lesser values in property than class_count
    """
    if method == "quantile":
        return discretize_quantile(geo_layer, field, class_count)
    elif method == "jenks":
        return discretize_jenks(geo_layer, field, class_count)
    elif method == "equal_interval":
        return discretize_equal_interval(geo_layer, field, class_count)
    else:
        raise ValueError(f'Unknow discretize method "{method}"')


def get_style_no_value_condition(key, with_value, with_no_value):
    if with_no_value is not None:
        if with_value is not None:
            return [
                "case",
                ["==", ["typeof", key], "number"],
                with_value,
                with_no_value,
            ]
        else:
            return with_no_value
    else:
        return with_value


def gen_style_steps(expression, boundaries, values):
    """
    Assume len(boundaries) <= len(colors) - 1
    """
    if len(boundaries) > 0:
        return ["step", expression, values[0]] + _flatten(
            zip(boundaries[1:], values[1:])
        )


def gen_style_interpolate(expression, boundaries, values):
    """
    Build a Mapbox GL Style interpolation expression.
    """
    return ["interpolate", ["linear"], expression] + _flatten(zip(boundaries, values))


def size_boundaries_candidate(min, max):
    return [(max - min) / 2]


def circle_boundaries_candidate(min, max):
    """
    Implementation of Self-Adjusting Legends for Proportional Symbol Maps
    https://pdfs.semanticscholar.org/d3f9/2bbd24ae83af6c101e5caacbd3e830d99272.pdf
    """
    if min is None or max is None:
        return []
    elif min <= 0:
        raise ValueError("Minimum value should be > 0")

    # array of base values in decreasing order in the range [1,10)
    bases = [5, 2.5, 1]
    # an index into the bases array
    base_id = 0
    # array that will hold the candidate values
    values = []
    # scale the minimum and maximum such that the minimum is > 1
    scale = 1  # scale factor
    min_s = min  # scaled minimum
    max_s = max  # scaled maximum
    while min_s < 1:
        min_s *= 10
        max_s *= 10
        scale /= 10

    # Compute the number of digits of the integral part of the scaled maximum
    ndigits = math.floor(math.log10(max_s))

    # Find the index into the bases array for the first limit smaller than max_s
    for i in range(0, len(bases)):
        if (max_s / 10**ndigits) >= bases[i]:
            base_id = i
            break

    while True:
        v = bases[base_id] * (10**ndigits)
        # stop the loop if the value is smaller than min_s
        if v <= min_s:
            break

        # otherwise store v in the values array
        values.append(
            v * scale
        )  # The the paper is false here, need mutiplication, no division
        # switch to the next base
        base_id += 1
        if base_id == len(bases):
            base_id = 0
            ndigits = ndigits - 1

    return values


def circle_boundaries_value_to_symbol_height(value, max_value, max_size):
    return math.sqrt(value / math.pi) * (max_size / math.sqrt(max_value / math.pi))


def circle_boundaries_filter_values(values, max_value, max_size, dmin):
    if not values or max_value is None or max_size is None:
        return []

    # array that will hold the filtered values
    filtered_values = []
    # add the maximum value
    filtered_values.append(values[0])
    # remember the height of the previously added value
    previous_height = circle_boundaries_value_to_symbol_height(
        values[0], max_value, max_size
    )
    # find the height and value of the smallest acceptable symbol
    last_height = 0
    last_value_id = len(values) - 1
    while last_value_id >= 0:
        last_height = circle_boundaries_value_to_symbol_height(
            values[last_value_id], max_value, max_size
        )
        if last_height > dmin:
            break
        last_value_id -= 1

    # loop over all values that are large enough
    for limit_id in range(1, last_value_id + 1):
        v = values[limit_id - 1]
        # compute the height of the symbol
        h = circle_boundaries_value_to_symbol_height(v, max_value, max_size)
        # do not draw the symbol if it is too close to the smallest symbol (but is not the smallest limit itself)
        if h - last_height < dmin and limit_id != last_value_id:
            continue
        # do not draw the symbol if it is too close to the previously drawn symbol
        if previous_height - h < dmin:
            continue
        filtered_values.append(v)
        # remember the height of the last drawn symbol
        previous_height = h

    return filtered_values


def lost_scale_digit(n, scale):
    """
    Return the number of digit to round
    """
    if n == 0:
        return 1  # Further in compuration 0 dived by 1 will be ok: 0
    else:
        return math.trunc(math.log10(n)) + 1 - scale


def trunc_scale(n, scale):
    lost = lost_scale_digit(n, scale)
    return math.trunc(n / (10**lost)) * (10**lost)


def round_scale(n, scale):
    lost = lost_scale_digit(n, scale)
    return round(n / (10**lost)) * (10**lost)


def ceil_scale(n, scale):
    lost = lost_scale_digit(n, scale)
    return math.ceil(n / (10**lost)) * (10**lost)


def boundaries_round(boundaries, scale=2):
    """
    Round boundaries to human readable number
    """
    return (
        [trunc_scale(boundaries[0], scale)]
        + [round_scale(b, scale) for b in boundaries[1:-2]]
        + [ceil_scale(boundaries[-1], scale)]
    )
