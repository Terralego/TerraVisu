from constance.test import override_config
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from project.terra_layer.tests.factories import SceneFactory
from project.visu.tests.factories import SpriteValueFactory


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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "allowUserRegistration": False,
                "credits": "Source: TerraVisu",
                "extraMenuItems": [],
                "favicon": "/static_dj/img/favicon.ico",
                "theme": {
                    "brandLogo": "/static_dj/img/splashscreen.png",
                    "logo": "/static_dj/img/logo.webp",
                    "logoUrl": "/",
                    "styles": [],
                },
                "title": "TerraVisu",
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
    )
    def test_custom(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "allowUserRegistration": False,
                "credits": "My Credits",
                "extraMenuItems": [],
                "favicon": "/media/favicon.ico",
                "theme": {
                    "brandLogo": "/media/splashscreen.png",
                    "logo": "/media/logo.webp",
                    "logoUrl": "https://example.com",
                    "styles": [],
                },
                "title": "My Title",
                "version": None,
            },
        )


class AdminSettingsApiView(APITestCase):
    url = reverse_lazy("settings-admin")

    def test_default_values(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "title": "TerraVisu",
                "theme": {
                    "logo": {
                        "src": "/static_dj/img/logo.webp",
                        "alt": "Logo",
                    },
                    "favicon": "/static_dj/img/favicon.ico",
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
    def test_custom(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "title": "TerraTest",
                "theme": {
                    "logo": {
                        "src": "/media/logo.png",
                        "alt": "Logo",
                    },
                    "favicon": "/media/favicon.ico",
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
        SceneFactory(name="custom name")
        self.client.get(self.url)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "API_HOST": "http://testserver/api",
                "DEFAULT_VIEWNAME": "custom-name",
                "VIEW_ROOT_PATH": "view",
            },
        )

    def test_custom_scene(self):
        SceneFactory(name="custom name 1")
        scene = SceneFactory(name="custom name 2")
        with override_config(DEFAULT_VIEW_NAME=scene.slug):
            self.client.get(self.url)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.data,
                {
                    "API_HOST": "http://testserver/api",
                    "DEFAULT_VIEWNAME": f"{scene.slug}",
                    "VIEW_ROOT_PATH": "view",
                },
            )
