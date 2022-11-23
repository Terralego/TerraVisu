from django.urls import reverse
from mapbox_baselayer.models import MapBaseLayer
from rest_framework.response import Response
from rest_framework.views import APIView
from project.visu import settings as app_settings


class SettingsView(APIView):
    def get(self, request, *args, **kwargs):
        base_layers = MapBaseLayer.objects.all()
        return Response({
            "instance": {
                "title": app_settings.INSTANCE_TITLE,
                "logo": app_settings.INSTANCE_LOGO,
                "loginUrl": reverse("login"),
                "logoutUrl": reverse("logout"),
            },
            "map": {
                "baseLayers": [
                    {"label": layer.name,
                     "slug": layer.slug,
                     "url": f"{layer.url}"
                     } for layer in base_layers
                ],
                "bounds": {
                    "minLat": app_settings.MAP_BBOX_LAT_MIN,
                    "minLon": app_settings.MAP_BBOX_LNG_MIN,
                    "maxLat": app_settings.MAP_BBOX_LAT_MAX,
                    "maxLon": app_settings.MAP_BBOX_LNG_MAX,
                },
                "zoom": {
                    "min": app_settings.MAP_MIN_ZOOM,
                    "max": app_settings.MAP_MAX_ZOOM,
                },
                "default": {
                    "lat": app_settings.MAP_DEFAULT_LAT,
                    "lng": app_settings.MAP_DEFAULT_LNG,
                    "zoom": app_settings.MAP_DEFAULT_ZOOM,
                }
            }
        })
