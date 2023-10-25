import logging
import os
from constance import config
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.timezone import now
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from project.accounts.serializers import UserSerializer
from project.terra_layer.models import Scene
from project.visu.models import ExtraMenuItem, SpriteValue
from project.visu.serializers import ExtraMenuItemSerializer

logger = logging.getLogger(__name__)


class CommonSettings:
    def get_logo_url(self):
        if config.INSTANCE_LOGO.startswith("/"):
            LOGO_URL = config.INSTANCE_LOGO
        else:
            LOGO_URL = default_storage.url(config.INSTANCE_LOGO)

        return self.request.build_absolute_uri(LOGO_URL)

    def get_favicon_url(self):
        if config.INSTANCE_FAVICON.startswith("/"):
            FAVICON_URL = config.INSTANCE_FAVICON
        else:
            FAVICON_URL = default_storage.url(config.INSTANCE_FAVICON)
        return self.request.build_absolute_uri(FAVICON_URL)

    def get_splashcreen_url(self):
        if config.INSTANCE_SPLASHSCREEN.startswith("/"):
            SPLASHSCREEN_URL = config.INSTANCE_SPLASHSCREEN
        else:
            SPLASHSCREEN_URL = default_storage.url(config.INSTANCE_SPLASHSCREEN)
        return self.request.build_absolute_uri(SPLASHSCREEN_URL)

    def get_user_token_data(self):
        user = (
            UserSerializer(self.request.user).data
            if self.request.user.is_authenticated
            else None
        )
        token = self.request.user.get_jwt_token() if user else None
        return user, token

    def get_sso_auth_config(self):
        if settings.OIDC_ENABLE_LOGIN:
            return {
                "loginUrl": reverse("login_dispatcher"),
                "logoutUrl": reverse("logout"),
                "ssoButtonText": config.OPENID_SSO_LOGIN_BUTTON_TEXT,
                "defaultButtonText": config.OPENID_DEFAULT_LOGIN_BUTTON_TEXT,
            }
        return {}

    def get_info_content(self):
        content = config.INSTANCE_INFO_CONTENT
        if not content:
            return render_to_string(
                "visu/info_menu_content.html",
                {"version": settings.VERSION, "year": now().year},
            )
        return content

    def get_sentry_settings(self):
        return {
            "dsn": settings.SENTRY_DSN,
            "environment": settings.SENTRY_ENVIRONMENT,
            "release": settings.SENTRY_RELEASE,
            "tracesSampleRate": settings.SENTRY_TRACE_SAMPLE_RATE,
            "replaysSessionSampleRate": settings.SENTRY_REPLAYS_SESSION_SAMPLE_RATE,
            "replaysOnErrorSampleRate": settings.SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE,
            "sendDefaultPii": settings.SENTRY_SEND_DEFAULT_PII,
        }


class SettingsAdminView(CommonSettings, APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        user, token = self.get_user_token_data()

        return Response(
            {
                "title": config.INSTANCE_TITLE,
                "theme": {
                    "logo": {
                        "src": self.get_logo_url(),
                        "alt": "Logo",
                    },
                    "favicon": self.get_favicon_url(),
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
                "token": token,
                "ssoAuth": self.get_sso_auth_config(),
                "spriteBaseUrl": reverse("sprites", request=request),
                "sentry": self.get_sentry_settings(),
            }
        )


class SettingsFrontendView(CommonSettings, APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        extra_menu_items_filters = Q(limit_to_groups__isnull=True)
        if request.user.is_authenticated:
            extra_menu_items_filters |= Q(limit_to_groups__in=request.user.groups.all())
        extra_menu_items = ExtraMenuItem.objects.filter(extra_menu_items_filters)

        user, token = self.get_user_token_data()
        return Response(
            {
                # deprecated section  & front
                "title": config.INSTANCE_TITLE,
                "version": None,
                "credits": config.INSTANCE_CREDITS,
                "favicon": self.get_favicon_url(),
                "theme": {
                    "logo": self.get_logo_url(),
                    "brandLogo": self.get_splashcreen_url(),
                    "logoUrl": config.INSTANCE_LOGO_FRONTEND_URL,
                    "styles": [],
                },
                "extraMenuItems": ExtraMenuItemSerializer(
                    extra_menu_items,
                    many=True,
                    context={"request": request},
                ).data,
                "infoContent": self.get_info_content(),
                "allowUserRegistration": False,
                "user": user,
                "token": token,
                "ssoAuth": self.get_sso_auth_config(),
                "frontendTools": {
                    "measureControl": {
                        "enable": config.MEASURE_CONTROL,
                        "styles": config.MEASURE_DRAW_STYLES,
                    },
                    "searchInLocations": {
                        "enable": config.SEARCH_IN_LOCATIONS,
                        "searchProvider": self._get_search_provider_config(),
                    },
                },
                "sentry": self.get_sentry_settings(),
            }
        )

    def _get_search_provider_config(self):
        provider_config = {
            "provider": config.SEARCH_IN_LOCATIONS_PROVIDER,
            "options": {},
        }

        if provider_config["provider"] == "nominatim":
            provider_config["baseUrl"] = config.NOMINATIM_URL
            provider_config["options"] = {}

            if config.NOMINATIM_USE_VIEWBOX:
                provider_config["options"]["viewbox"] = [
                    config.NOMINATIM_VIEWBOX_MIN_LONG or config.MAP_BBOX_LNG_MIN,
                    config.NOMINATIM_VIEWBOX_MIN_LAT or config.MAP_BBOX_LAT_MIN,
                    config.NOMINATIM_VIEWBOX_MAX_LONG or config.MAP_BBOX_LNG_MAX,
                    config.NOMINATIM_VIEWBOX_MAX_LAT or config.MAP_BBOX_LAT_MAX,
                ]
        return provider_config


class EnvFrontendView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        default_scene = Scene.objects.get_user_scenes(request.user).first()

        if not default_scene:
            raise Exception("You should defined a scene with at least one layer")
        default_view = default_scene.slug

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
