from project.terra_layer.settings import DEFAULT_NO_VALUE_FILL_COLOR

from .all import gen_categorized_any_legend, gen_categorized_any_style
from .color import gen_graduated_color_legend, gen_graduated_color_style
from .radius import gen_proportionnal_radius_legend, gen_proportionnal_radius_style
from .size import (
    gen_graduated_size_legend,
    gen_graduated_size_style,
    gen_proportionnal_size_legend,
    gen_proportionnal_size_style,
)
from .utils import get_style_no_value_condition, style_type_2_legend_property


def to_map_style(prop):
    return prop.replace("_", "-")


def field_2_variation_type(field):
    if "color" in field:
        return "color"
    if (
        "width" in field
        or "height" in field
        or "opacity" in field
        or "intensity" in field
        or "size" in field
    ):
        return "value"
    if "radius" in field:
        return "radius"


def get_paint_or_layout(field):
    if field in [
        "icon-image",
        "icon-size",
        "text-field",
        "text-font",
        "text-size",
        "text-allow-overlap",
        "fill-sort-key",
        "line-sort-key",
    ]:
        return "layout"
    return "paint"


def get_layer_type(map_style_type):
    if map_style_type in ["icon", "text"]:
        return "symbol"
    return map_style_type


def generate_style_from_wizard(geo_layer, config):
    """
    Return a Mapbox GL Style and a Legend from a wizard setting.
    """

    # fill, fill_extrusion, line, text, symbol, circle
    map_style_type = config.get("map_style_type", {})
    suid = config["uid"]

    map_style = {"type": get_layer_type(map_style_type)}

    if "min_zoom" in config:
        map_style["minzoom"] = config["min_zoom"]
    if "max_zoom" in config:
        map_style["maxzoom"] = config["max_zoom"]
    if "weight" in config:
        map_style["weight"] = config["weight"]

    legends = []

    for map_field, prop_config in config.get("style", {}).items():
        style_type = prop_config.get("type", "none")

        # Ignore style from other representation
        if not map_field.replace("fill_extrusion", "extrusion").startswith(
            map_style_type.replace("fill-extrusion", "extrusion")
        ):
            continue

        map_style_prop = to_map_style(map_field)
        paint_or_layout = get_paint_or_layout(map_style_prop)
        if style_type == "fixed":
            # Fixed value
            value = prop_config["value"]
            no_value = prop_config.get("no_value")
            data_field = prop_config.get("field")
            map_style.setdefault(paint_or_layout, {})[
                map_style_prop
            ] = get_style_no_value_condition(["get", data_field], value, no_value)
        elif style_type == "variable":
            # Variable style
            data_field = prop_config["field"]
            variation_type = field_2_variation_type(map_field)
            analysis = prop_config["analysis"]

            if variation_type == "color":
                if analysis == "graduated":
                    map_style.setdefault(paint_or_layout, {})[
                        map_style_prop
                    ] = gen_graduated_color_style(
                        geo_layer, data_field, map_field, prop_config
                    )
                    if prop_config.get("generate_legend"):
                        legend = gen_graduated_color_legend(
                            geo_layer,
                            data_field,
                            map_style_type,
                            prop_config,
                            style_type_2_legend_property(map_field),
                        )
                        legend["uid"] = f"{suid}__{map_field}"
                        # TODO reuse previous computations
                        legends.append(legend)
                elif analysis == "categorized":
                    map_style.setdefault(paint_or_layout, {})[
                        map_style_prop
                    ] = gen_categorized_any_style(
                        geo_layer, data_field, prop_config, DEFAULT_NO_VALUE_FILL_COLOR
                    )
                    if (
                        map_style.setdefault(paint_or_layout, {})[map_style_prop]
                        is None
                    ):
                        del map_style.setdefault(paint_or_layout, {})[map_style_prop]

                    if prop_config.get("generate_legend"):
                        legend = gen_categorized_any_legend(
                            map_style_type,
                            prop_config,
                            style_type_2_legend_property(map_field),
                        )
                        legend["uid"] = f"{suid}__{map_field}"
                        legends.append(legend)
                else:
                    raise ValueError(f'Unhandled analysis type "{analysis}"')

            if variation_type == "radius":
                if analysis == "categorized":
                    generated_style = gen_categorized_any_style(
                        geo_layer, data_field, prop_config, 0
                    )
                    if generated_style:
                        map_style.setdefault(paint_or_layout, {})[
                            map_style_prop
                        ] = generated_style
                    """if (
                        map_style[paint_or_layout][map_style_prop]
                        is None
                    ):
                        del map_style[paint_or_layout][map_style_prop]"""

                    if prop_config.get("generate_legend"):
                        color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("value", DEFAULT_NO_VALUE_FILL_COLOR)
                        )
                        legend = gen_categorized_any_legend(
                            map_style_type,
                            prop_config,
                            style_type_2_legend_property(map_field),
                            other_properties={"color": color},
                        )
                        legend["uid"] = f"{suid}__{map_field}"
                        legends.append(legend)

                elif analysis == "proportionnal":
                    map_style.setdefault(paint_or_layout, {})[
                        map_style_prop
                    ] = gen_proportionnal_radius_style(
                        geo_layer, data_field, map_field, prop_config
                    )
                    # Add sort key
                    # TODO find more smart way to do that
                    map_style["layout"] = {
                        f"{map_style_type}-sort-key": ["-", ["get", data_field]]
                    }
                    if prop_config.get("generate_legend"):
                        # TODO reuse previous computations
                        color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("value", DEFAULT_NO_VALUE_FILL_COLOR)
                        )
                        no_value_color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("no_value")
                        )
                        legend = gen_proportionnal_radius_legend(
                            geo_layer,
                            data_field,
                            map_style_type,
                            prop_config,
                            color,
                            no_value_color,
                        )
                        legend["uid"] = f"{suid}__{map_field}"
                        legends.append(legend)
                else:
                    raise ValueError(f'Unhandled analysis type "{analysis}"')

            if variation_type == "value":
                if analysis == "graduated":
                    map_style.setdefault(paint_or_layout, {})[
                        map_style_prop
                    ] = gen_graduated_size_style(
                        geo_layer, data_field, map_field, prop_config
                    )
                    if prop_config.get("generate_legend"):
                        # TODO reuse previous computations
                        color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("value", DEFAULT_NO_VALUE_FILL_COLOR)
                        )
                        no_value_color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("no_value")
                        )
                        legend = gen_graduated_size_legend(
                            geo_layer,
                            data_field,
                            map_style_type,
                            prop_config,
                            color,
                            no_value_color,
                            style_type_2_legend_property(map_field),
                        )
                        legend["uid"] = f"{suid}__{map_field}"
                        legends.append(legend)

                elif analysis == "categorized":
                    generated_style = gen_categorized_any_style(
                        geo_layer, data_field, prop_config, 0
                    )
                    if generated_style:
                        map_style.setdefault(paint_or_layout, {})[
                            map_style_prop
                        ] = generated_style

                    if prop_config.get("generate_legend"):
                        color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("value", DEFAULT_NO_VALUE_FILL_COLOR)
                        )
                        legend = gen_categorized_any_legend(
                            map_style_type,
                            prop_config,
                            style_type_2_legend_property(map_field),
                            other_properties={"color": color},
                        )
                        legend["uid"] = f"{suid}__{map_field}"
                        legends.append(legend)

                elif analysis == "proportionnal":
                    """map_style["layout"] = {
                        f"{map_style_type}-sort-key": ["-", ["get", data_field]]
                    }"""
                    map_style.setdefault(paint_or_layout, {})[
                        map_style_prop
                    ] = gen_proportionnal_size_style(
                        geo_layer, data_field, map_field, prop_config
                    )
                    if prop_config.get("generate_legend"):
                        # TODO reuse previous computations
                        color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("value", DEFAULT_NO_VALUE_FILL_COLOR)
                        )
                        no_value_color = (
                            config["style"]
                            .get(f"{map_style_type}_color", {})
                            .get("no_value")
                        )
                        legend = gen_proportionnal_size_legend(
                            geo_layer,
                            data_field,
                            map_style_type,
                            prop_config,
                            color,
                            no_value_color,
                            style_type_2_legend_property(map_field),
                        )
                        legend["uid"] = f"{suid}__{map_field}"
                        legends.append(legend)
                else:
                    raise ValueError(f'Unknow analysis type "{analysis}"')

    return (map_style, legends)
