from django.conf import settings

default_settings = getattr(settings, "TERRA_LAYER_STYLE_SETTINGS", {})

# Min height between circle legend labels, in pixels. Typically based on label police size.
DEFAULT_CIRCLE_MIN_LEGEND_HEIGHT = default_settings.get("circle_min_legend_height", 14)
DEFAULT_SIZE_MIN_LEGEND_HEIGHT = default_settings.get("size_min_legend_height", 1)
DEFAULT_NO_VALUE_FILL_COLOR = default_settings.get("no_value_fill_color", "#000000")
