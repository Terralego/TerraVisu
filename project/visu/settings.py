from django.conf import settings
from django.db.models import ImageField
from siteprefs.toolbox import preferences

INSTANCE_TITLE = getattr(settings, "INSTANCE_TITLE", "TerraVisu")
INSTANCE_LOGO = getattr(settings, "INSTANCE_LOGO", "/static/img/logo.webp")
MAP_BBOX_LNG_MIN = getattr(settings, "MAP_BBOX_LNG_MIN", -180.0)
MAP_BBOX_LNG_MAX = getattr(settings, "MAP_BBOX_LNG_MAX", 180.0)
MAP_BBOX_LAT_MIN = getattr(settings, "MAP_BBOX_LAT_MIN", -90.0)
MAP_BBOX_LAT_MAX = getattr(settings, "MAP_BBOX_LAT_MAX", 90.0)
MAP_MAX_ZOOM = getattr(settings, "MAP_MAX_ZOOM", 23.0)
MAP_MIN_ZOOM = getattr(settings, "MAP_MIN_ZOOM", 0.0)
MAP_DEFAULT_ZOOM = getattr(settings, "MAP_DEFAULT_ZOOM", 7.0)
MAP_DEFAULT_LNG = getattr(settings, "MAP_DEFAULT_LNG", 2.0)
MAP_DEFAULT_LAT = getattr(settings, "MAP_DEFAULT_LAT", 44.0)

with preferences() as prefs:
    prefs(  # Now we register our settings to make them available as siteprefs.
        # First we define a group of related settings, and mark them non-static (editable).
        prefs.group(
            "Instance",
            (
                INSTANCE_TITLE,
                prefs.one(
                    INSTANCE_LOGO, static=False, field=ImageField(upload_to="logos/")
                ),
            ),
            static=False,
        ),
        prefs.group(
            "Map BBox",
            (MAP_BBOX_LNG_MIN, MAP_BBOX_LNG_MAX, MAP_BBOX_LAT_MIN, MAP_BBOX_LAT_MAX),
            static=False,
        ),
        prefs.group("Map Zoom", (MAP_MAX_ZOOM, MAP_MIN_ZOOM), static=False),
        prefs.group(
            "Map default center",
            (MAP_DEFAULT_ZOOM, MAP_DEFAULT_LNG, MAP_DEFAULT_LAT),
            static=False,
        ),
    )
