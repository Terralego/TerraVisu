from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

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
            {
                sprite_value.slug: {
                    "height": 10,
                    "pixelRatio": 1,
                    "visible": True,
                    "width": 10,
                    "x": 0,
                    "y": 0,
                }
            },
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
