import logging

from constance import config
from django.core.files.storage import default_storage
from django.db.models import Q
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from project.accounts.serializers import UserSerializer
from project.terra_layer.models import Scene
from project.visu.models import ExtraMenuItem, SpriteValue
from project.visu.serializers import ExtraMenuItemSerializer

logger = logging.getLogger(__name__)


class SettingsAdminView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        user = (
            UserSerializer(request.user).data if request.user.is_authenticated else None
        )
        from django.core.files.storage import default_storage

        if config.INSTANCE_LOGO.startswith("/"):
            LOGO_URL = config.INSTANCE_LOGO
        else:
            LOGO_URL = default_storage.url(config.INSTANCE_LOGO)

        if config.INSTANCE_FAVICON.startswith("/"):
            FAVICON_URL = config.INSTANCE_FAVICON
        else:
            FAVICON_URL = default_storage.url(config.INSTANCE_FAVICON)

        return Response(
            {
                "title": config.INSTANCE_TITLE,
                "theme": {
                    "logo": {
                        "src": LOGO_URL,
                        "alt": "Logo",
                    },
                    "favicon": FAVICON_URL,
                    "heading": "<h2>Administration</h2>",
                },
                "map": {
                    "accessToken": config.MAPBOX_ACCESS_TOKEN,
                    "bounds": {
                        "minLat": config.MAP_BBOX_LAT_MIN,
                        "minLon": config.MAP_BBOX_LNG_MIN,
                        "maxLat": config.MAP_BBOX_LAT_MAX,
                        "maxLon": config.MAP_BBOX_LNG_MAX,
                    },
                    "zoom": config.MAP_DEFAULT_ZOOM,
                    "center": [config.MAP_DEFAULT_LNG, config.MAP_DEFAULT_LAT],
                },
                "user": user,
                "spriteBaseUrl": reverse("sprites", request=request),
            }
        )


class SettingsFrontendView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        if config.INSTANCE_LOGO.startswith("/"):
            LOGO_URL = config.INSTANCE_LOGO
        else:
            LOGO_URL = default_storage.url(config.INSTANCE_LOGO)

        if config.INSTANCE_SPLASHSCREEN.startswith("/"):
            INSTANCE_SPLASHSCREEN = config.INSTANCE_SPLASHSCREEN
        else:
            INSTANCE_SPLASHSCREEN = default_storage.url(config.INSTANCE_SPLASHSCREEN)

        if config.INSTANCE_FAVICON.startswith("/"):
            FAVICON_URL = config.INSTANCE_FAVICON
        else:
            FAVICON_URL = default_storage.url(config.INSTANCE_FAVICON)
        extra_menu_items_filters = Q(limit_to_groups__isnull=True)
        if request.user.is_authenticated:
            extra_menu_items_filters |= Q(limit_to_groups__in=request.user.groups.all())
        extra_menu_items = ExtraMenuItem.objects.filter(extra_menu_items_filters)

        return Response(
            {
                # deprecated section  & front
                "title": config.INSTANCE_TITLE,
                "version": None,
                "credits": config.INSTANCE_CREDITS,
                "favicon": FAVICON_URL,
                "theme": {
                    "logo": LOGO_URL,
                    "brandLogo": INSTANCE_SPLASHSCREEN,
                    "logoUrl": config.INSTANCE_LOGO_FRONTEND_URL,
                    "styles": [],
                },
                "extraMenuItems": ExtraMenuItemSerializer(
                    extra_menu_items,
                    many=True,
                    context={"request": request},
                ).data,
                "allowUserRegistration": False,
            }
        )


class EnvFrontendView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        default_view = config.DEFAULT_VIEW_NAME
        if not config.DEFAULT_VIEW_NAME:
            logger.warning(
                "No default scene define in /config/. Trying to find first scene with layers..."
            )
            scene = Scene.objects.first()
            if not scene:
                raise Exception("You should defined a scene with at least one layer")
            default_view = scene.slug

        return Response(
            {
                "API_HOST": request.build_absolute_uri("/api"),
                "VIEW_ROOT_PATH": config.VIEW_ROOT_PATH,
                "DEFAULT_VIEWNAME": default_view,
            }
        )


class SpriteDataAPIView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        data = {}
        for sv in SpriteValue.objects.all():
            data[sv.slug] = {}
        return Response(data)
