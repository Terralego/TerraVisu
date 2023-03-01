from constance import config
from django.urls import reverse
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from project.accounts.serializers import UserSerializer


class SettingsView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        base_layers = MapBaseLayer.objects.all()
        user = (
            UserSerializer(request.user).data if request.user.is_authenticated else None
        )
        from django.core.files.storage import default_storage

        if default_storage.exists(config.INSTANCE_LOGO):
            LOGO_URL = default_storage.url(config.INSTANCE_LOGO)
        else:
            LOGO_URL = config.INSTANCE_LOGO

        if default_storage.exists(config.INSTANCE_FAVICON):
            FAVICON_URL = default_storage.url(config.INSTANCE_FAVICON)
        else:
            FAVICON_URL = config.INSTANCE_FAVICON
        return Response(
            {
                # deprecated section
                "title": config.INSTANCE_TITLE,
                "theme": {
                    "logo": {
                        "src": LOGO_URL,
                        "alt": "Logo",
                    },
                    "favicon": FAVICON_URL,
                    "heading": "<h2>Administration</h2>",
                },
                # end deprecated section
                "instance": {
                    "title": config.INSTANCE_TITLE,
                    "logo": LOGO_URL,
                    "loginUrl": reverse("login_dispatcher"),
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
                        "minLat": config.MAP_BBOX_LAT_MIN,
                        "minLon": config.MAP_BBOX_LNG_MIN,
                        "maxLat": config.MAP_BBOX_LAT_MAX,
                        "maxLon": config.MAP_BBOX_LNG_MAX,
                    },
                    "zoom": {
                        "min": config.MAP_MIN_ZOOM,
                        "max": config.MAP_MAX_ZOOM,
                    },
                    "default": {
                        "lat": config.MAP_DEFAULT_LAT,
                        "lng": config.MAP_DEFAULT_LNG,
                        "zoom": config.MAP_DEFAULT_ZOOM,
                    },
                },
                "user": user,
            }
        )
