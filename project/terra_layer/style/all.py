from .utils import style_type_2_legend_shape


def gen_categorized_any_style(geo_layer, data_field, prop_config, default_no_value):
    default_value = None
    field_getter = ["get", data_field]

    if not prop_config["categories"]:
        return None

    steps = ["match", field_getter]
    for category in prop_config["categories"]:
        name = category["name"]
        value = category["value"]
        if name is None:
            default_value = value
            continue

        steps.append(name)
        steps.append(value)

    steps.append(default_value or default_no_value)

    if default_value is not None:
        return ["case", ["has", data_field], steps, default_value]
    else:
        return steps


def gen_categorized_any_legend(
    map_style_type,
    prop_config,
    legend_field="size",
    other_properties=None,
):
    other_properties = other_properties or {}

    default_value = None
    shape = style_type_2_legend_shape.get(map_style_type, "square")

    items = []
    for category in prop_config["categories"]:
        name = category["name"]
        value = category["value"]
        if name is None:
            default_value = value
            continue

        items.append({legend_field: value, "label": name, **other_properties})

    if default_value is not None:
        items.append({legend_field: value, "label": None, **other_properties})

    return {"shape": shape, "items": items}
