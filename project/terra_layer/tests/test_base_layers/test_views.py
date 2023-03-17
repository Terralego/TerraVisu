from io import StringIO

from django.core.management import call_command
from django.urls import reverse
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import status
from rest_framework.test import APITestCase

from project.accounts.tests.factories import SuperUserFactory


class MapBaseLayerViewsSetTesCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        out = StringIO()
        call_command("install_osm_baselayer", stdout=out)
        cls.mapbox = MapBaseLayer.objects.create(
            name="mapbox", base_layer_type="mapbox", map_box_url="mapbox://test/"
        )
        cls.user = SuperUserFactory()

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_list(self):
        response = self.client.get(reverse("baselayer-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(len(data["results"]) > 0)

    def test_detail_raster(self):
        pk = MapBaseLayer.objects.get(slug="osm").pk
        response = self.client.get(reverse("baselayer-detail", args=(pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "OSM")

    def test_detail_mapbox(self):
        response = self.client.get(reverse("baselayer-detail", args=(self.mapbox.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "mapbox")

    def test_tilejson_url_in_list(self):
        response = self.client.get(reverse("baselayer-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(len(data["results"]) > 1)
        self.assertEqual(
            data["results"][1]["tilejson_url"],
            "http://testserver/api/baselayer/1/tilejson/",
        )

    def test_tilejson_in_list(self):
        pk = MapBaseLayer.objects.get(slug="osm").pk
        response = self.client.get(reverse("baselayer-detail", args=(pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        tilejson_url = data["tilejson_url"]
        response = self.client.get(tilejson_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json())

    def test_create(self):
        data = {
            "tiles": [
                "//test.org",
            ],
            "name": "test",
            "order": 0,
            "base_layer_type": "raster",
            "min_zoom": 0,
            "max_zoom": 20,
            "tile_size": 256,
        }
        response = self.client.post(reverse("baselayer-list"), data=data)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, data)

        self.assertTrue(data["id"])
        self.assertEqual(data["tiles"][0], "//test.org")

    def test_partial_update(self):
        data = {
            "tiles": [
                "//test2.org",
            ],
        }
        pk = MapBaseLayer.objects.first().pk
        response = self.client.patch(reverse("baselayer-detail", args=(pk,)), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["tiles"][0], "//test2.org")

    def test_full_update(self):
        data = {
            "tiles": [
                "//test3.org",
            ],
            "name": "test",
            "order": 0,
            "base_layer_type": "raster",
            "min_zoom": 0,
            "max_zoom": 20,
            "tile_size": 256,
        }
        pk = MapBaseLayer.objects.first().pk
        response = self.client.patch(reverse("baselayer-detail", args=(pk,)), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["tiles"][0], "//test3.org")

    def test_delete(self):
        pk = MapBaseLayer.objects.first().pk
        response = self.client.delete(reverse("baselayer-detail", args=(pk,)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
