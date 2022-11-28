from django.urls import reverse
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from project.accounts.serializers import UserSerializer

from . import settings as app_settings


class SettingsView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        base_layers = MapBaseLayer.objects.all()
        user = (
            UserSerializer(request.user).data if request.user.is_authenticated else None
        )

        return Response(
            {
                "instance": {
                    "title": app_settings.INSTANCE_TITLE,
                    "logo": app_settings.INSTANCE_LOGO,
                    "loginUrl": reverse("login"),
                    "logoutUrl": reverse("logout"),
                },
                "map": {
                    "baseLayers": [
                        {
                            "label": layer.name,
                            "slug": layer.slug,
                            "url": f"{request.build_absolute_uri(layer.url)}"
                            if layer.url.startswith("/")
                            else f"{layer.url}",
                        }
                        for layer in base_layers
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
                    },
                },
                "user": user,
            }
        )
