from constance.test import override_config
from django.contrib.auth.models import Group
from django.test import RequestFactory, override_settings
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from project.accounts.tests.factories import UserFactory
from project.terra_layer.tests.factories import LayerFactory, LayerGroupFactory
from project.visu.api import CommonSettings
from project.visu.serializers import ExtraMenuItemSerializer
from project.visu.tests.factories import ExtraMenuItemFactory, SpriteValueFactory


class SpriteDataAPIViewTestCase(APITestCase):
    url = reverse_lazy("sprites")

    def test_empty_value(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {})

    def test_values(self):
        sprite_value = SpriteValueFactory()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {sprite_value.slug: {}},
        )


class FrontendSettingsAPIViewTestCase(APITestCase):
    url = reverse_lazy("settings-frontend")

    def test_default_values(self):
        self.maxDiff = None
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "allowUserRegistration": False,
                "credits": "Source: TerraVisu",
                "frontendTools": {
                    "measureControl": {
                        "enable": False,
                        "styles": [],
                    },
                    "searchInLocations": {
                        "enable": False,
                        "searchProvider": "https://nominatim.openstreetmap.org/search?",
                        "viewbox": [-180.0, -90.0, 180.0, 90.0],
                    },
                },
                "ssoAuth": {},
                "extraMenuItems": [],
                "favicon": "http://testserver/static_dj/img/favicon.ico",
                "infoContent": CommonSettings().get_info_content(),
                "theme": {
                    "brandLogo": "http://testserver/static_dj/img/splashscreen.png",
                    "logo": "http://testserver/static_dj/img/logo.webp",
                    "logoUrl": "/",
                    "styles": [],
                },
                "title": "TerraVisu",
                "token": None,
                "user": None,
                "version": None,
            },
        )

    @override_config(
        INSTANCE_TITLE="My Title",
        INSTANCE_CREDITS="My Credits",
        INSTANCE_LOGO_FRONTEND_URL="https://example.com",
        INSTANCE_LOGO="logo.webp",
        INSTANCE_SPLASHSCREEN="splashscreen.png",
        INSTANCE_FAVICON="favicon.ico",
        OPENID_SSO_LOGIN_BUTTON_TEXT="Login via SSO",
        OPENID_DEFAULT_LOGIN_BUTTON_TEXT="Login via internal",
        INSTANCE_INFO_CONTENT="<b>This is my info content</b>",
    )
    @override_settings(OIDC_ENABLE_LOGIN=True)
    def test_custom(self):
        self.maxDiff = None
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "allowUserRegistration": False,
                "credits": "My Credits",
                "extraMenuItems": [],
                "frontendTools": {
                    "measureControl": {
                        "enable": False,
                        "styles": [],
                    },
                    "searchInLocations": {
                        "enable": False,
                        "searchProvider": "https://nominatim.openstreetmap.org/search?",
                        "viewbox": [-180.0, -90.0, 180.0, 90.0],
                    },
                },
                "ssoAuth": {
                    "defaultButtonText": "Login via internal",
                    "loginUrl": "/api/auth/login/",
                    "logoutUrl": "/accounts/logout/",
                    "ssoButtonText": "Login via SSO",
                },
                "favicon": "http://testserver/media/favicon.ico",
                "infoContent": "<b>This is my info content</b>",
                "theme": {
                    "brandLogo": "http://testserver/media/splashscreen.png",
                    "logo": "http://testserver/media/logo.webp",
                    "logoUrl": "https://example.com",
                    "styles": [],
                },
                "title": "My Title",
                "token": None,
                "user": None,
                "version": None,
            },
        )

    def test_no_extra_menu_items(self):
        """With no extra menu item, array is empty"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["extraMenuItems"], [])

    def test_extra_menu_items_unauthenticated_without_groups(self):
        """Only extra menu items without group limit should be returned for unauthenticated users."""
        # add extra menu item with no group limit
        extra_menu_for_all = ExtraMenuItemFactory()
        # add extra menu item with group limit
        group = Group.objects.create(name="test")
        extra_menu = ExtraMenuItemFactory()
        extra_menu.limit_to_groups.add(group)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            response.data["extraMenuItems"],
            ExtraMenuItemSerializer(
                [extra_menu_for_all],
                many=True,
                context={"request": RequestFactory().get("/")},
            ).data,
        )

    def test_extra_menu_items_authenticated_without_groups(self):
        self.maxDiff = None
        user = UserFactory()
        self.client.force_authenticate(user)
        # add extra menu item with no group limit
        extra_menu_for_all = ExtraMenuItemFactory()
        # add extra menu item with group limit
        group_user = Group.objects.create(name="test")
        group_user.user_set.add(user)
        groupwithout_user = Group.objects.create(name="test2")
        extra_menu_for_group_user = ExtraMenuItemFactory()
        extra_menu_for_group_user.limit_to_groups.add(group_user)
        extra_menu_for_other_group = ExtraMenuItemFactory()
        extra_menu_for_other_group.limit_to_groups.add(groupwithout_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            sorted(response.data["extraMenuItems"], key=lambda x: x["id"]),
            sorted(
                ExtraMenuItemSerializer(
                    [extra_menu_for_all, extra_menu_for_group_user],
                    many=True,
                    context={"request": RequestFactory().get("/")},
                ).data,
                key=lambda x: x["id"],
            ),
        )

    def test_extra_menu_items_authenticated_with_groups(self):
        # self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["extraMenuItems"], [])


class AdminSettingsApiView(APITestCase):
    url = reverse_lazy("settings-admin")

    def test_default_values(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "title": "TerraVisu",
                "ssoAuth": {},
                "theme": {
                    "logo": {
                        "src": "http://testserver/static_dj/img/logo.webp",
                        "alt": "Logo",
                    },
                    "favicon": "http://testserver/static_dj/img/favicon.ico",
                    "heading": "<h2>Administration</h2>",
                },
                "map": {
                    "accessToken": "",
                    "bounds": {
                        "minLat": -90.0,
                        "minLon": -180.0,
                        "maxLat": 90.0,
                        "maxLon": 180.0,
                    },
                    "zoom": 7.0,
                    "center": [2.0, 44.0],
                },
                "user": None,
                "token": None,
                "spriteBaseUrl": "http://testserver/api/sprites",
            },
        )

    @override_config(
        INSTANCE_TITLE="TerraTest",
        INSTANCE_LOGO="logo.png",
        INSTANCE_FAVICON="favicon.ico",
        MAPBOX_ACCESS_TOKEN="token",
        MAP_BBOX_LNG_MIN=-110.0,
        MAP_BBOX_LNG_MAX=120.0,
        MAP_BBOX_LAT_MIN=-43.0,
        MAP_BBOX_LAT_MAX=42.0,
        MAP_DEFAULT_LNG=1.0,
        MAP_DEFAULT_LAT=48.0,
        MAP_DEFAULT_ZOOM=6.0,
    )
    @override_settings(OIDC_ENABLE_LOGIN=True)
    def test_custom(self):
        self.maxDiff = None
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            {
                "title": "TerraTest",
                "ssoAuth": {
                    "defaultButtonText": "",
                    "loginUrl": "/api/auth/login/",
                    "logoutUrl": "/accounts/logout/",
                    "ssoButtonText": "",
                },
                "theme": {
                    "logo": {
                        "src": "http://testserver/media/logo.png",
                        "alt": "Logo",
                    },
                    "favicon": "http://testserver/media/favicon.ico",
                    "heading": "<h2>Administration</h2>",
                },
                "map": {
                    "accessToken": "token",
                    "bounds": {
                        "minLat": -43.0,
                        "minLon": -110.0,
                        "maxLat": 42.0,
                        "maxLon": 120.0,
                    },
                    "zoom": 6.0,
                    "center": [1.0, 48.0],
                },
                "user": None,
                "token": None,
                "spriteBaseUrl": "http://testserver/api/sprites",
            },
        )


class EnvJSONTestCase(APITestCase):
    url = reverse_lazy("env-front")

    def test_no_scene(self):
        with self.assertRaises(
            Exception, msg="You should defined a scene with at least one layer"
        ):
            self.client.get(self.url)

    def test_default_values(self):
        layer_group = LayerGroupFactory(label="custom name")
        LayerFactory(name="custom name", group=layer_group)
        self.client.get(self.url)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            {
                "API_HOST": "http://testserver/api",
                "VIEW_ROOT_PATH": "view",
                "DEFAULT_VIEWNAME": layer_group.view.slug,
            },
        )
