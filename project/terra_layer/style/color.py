from .utils import (
    discretize,
    gen_style_steps,
    get_style_no_value_condition,
    style_type_2_legend_shape,
)


def gen_color_legend_steps(boundaries, colors, no_value_color, legend_field="color"):
    """
    Generate a discrete color legend.
    """
    size = len(boundaries) - 1
    ret = [
        {
            legend_field: colors[index],
            "boundaries": {
                "lower": {"value": boundaries[index], "included": True},
                "upper": {
                    "value": boundaries[index + 1],
                    "included": index + 1 == size,
                },
            },
        }
        for index in range(size)
    ]

    if no_value_color:
        ret.insert(
            0,
            {
                legend_field: no_value_color,
                "boundaries": {
                    "lower": {"value": None, "included": True},
                    "upper": {"value": None, "included": True},
                },
            },
        )

    return ret


def gen_graduated_color_style(geo_layer, data_field, map_field, prop_config):
    colors = prop_config["values"]
    no_value = prop_config.get("no_value")

    # Step 1 generate boundaries
    if "boundaries" in prop_config:
        boundaries = prop_config["boundaries"]
        if len(boundaries) < 2:
            raise ValueError('"boundaries" must be at least a list of two values')
    elif "method" in prop_config:
        boundaries = discretize(
            geo_layer, data_field, prop_config["method"], len(colors)
        )
    else:
        raise ValueError(
            'With "graduated" analysis, "boundaries" or "method" should be provided'
        )

    # Use boundaries to make style
    if boundaries is not None:
        field_getter = ["get", data_field]

        style_steps = gen_style_steps(field_getter, boundaries, colors)

        return get_style_no_value_condition(
            field_getter,
            style_steps,
            no_value,
        )
    else:
        return no_value or colors[0]


def gen_graduated_color_legend(
    geo_layer, data_field, map_style_type, prop_config, legend_field
):
    colors = prop_config["values"]
    no_value = prop_config.get("no_value")

    # Step 1 generate boundaries
    if "boundaries" in prop_config:
        boundaries = prop_config["boundaries"]
    elif "method" in prop_config:
        boundaries = discretize(
            geo_layer, data_field, prop_config["method"], len(colors)
        )

    # Use boundaries to make style
    if boundaries is not None:
        return {
            "items": gen_color_legend_steps(boundaries, colors, no_value, legend_field)[
                ::-1
            ],
            "shape": style_type_2_legend_shape.get(map_style_type, "square"),
        }
    else:
        color = colors[0]
        if no_value:
            color = no_value

        return {
            "items": [
                {
                    legend_field: color,
                    "boundaries": {
                        "lower": {"value": None, "included": True},
                        "upper": {"value": None, "included": True},
                    },
                }
            ],
            "shape": style_type_2_legend_shape.get(map_style_type, "square"),
        }
