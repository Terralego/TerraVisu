from django.conf import settings
from django.core.management.base import BaseCommand
from mapbox_baselayer.models import MapBaseLayer


class Command(BaseCommand):
    help = "Populate database with default baselayer found in settings"

    def handle(self, **options):
        default_map_settings = settings.TERRA_DEFAULT_MAP_SETTINGS
        background_styles = default_map_settings.get("backgroundStyle", [])
        min_zoom = default_map_settings.get("minZoom", 0)
        max_zoom = default_map_settings.get("maxZoom", 24)

        if type(background_styles) is str:
            baselayer, _ = MapBaseLayer.objects.update_or_create(
                name="Default",
                defaults=dict(
                    map_box_url=background_styles,
                    base_layer_type="mapbox",
                    tile_size=512,
                    min_zoom=min_zoom,
                    max_zoom=max_zoom,
                ),
            )
            print(f"Baselayer created/updated '{baselayer.name}'")
        else:
            for i, bg_style in enumerate(background_styles):
                baselayer, _ = MapBaseLayer.objects.update_or_create(
                    name=bg_style.get("label", f"Default_{i+1}"),
                    defaults=dict(
                        map_box_url=bg_style["url"],
                        base_layer_type="mapbox",
                        tile_size=512,
                        min_zoom=min_zoom,
                        max_zoom=max_zoom,
                    ),
                )
                print(f"Baselayer created/update '{baselayer.name}'")
