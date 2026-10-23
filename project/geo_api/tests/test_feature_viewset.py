from unittest import mock

from django.contrib.gis.geos import Point
from geostore.models import Feature, Layer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from project.geo_api.serializers import FeatureGeoSerializer, FeatureListSerializer
from project.geo_api.views.feature_viewset import FeatureViewSet

from .base import BaseGeoAPITestCase


class FeatureViewSetTestCase(BaseGeoAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.layer = Layer.objects.create(name="feat_layer")
        cls.f1 = Feature.objects.create(
            layer=cls.layer,
            geom=Point(1.44, 43.60),
            identifier="feat-tls",
            properties={"name": "Toulouse", "dept": "31", "pop": 490000},
        )
        cls.f2 = Feature.objects.create(
            layer=cls.layer,
            geom=Point(2.35, 48.85),
            identifier="feat-prs",
            properties={"name": "Paris", "dept": "75", "pop": 2160000},
        )
        cls.f3 = Feature.objects.create(
            layer=cls.layer,
            geom=Point(4.83, 45.76),
            identifier="feat-lyn",
            properties={"name": "Lyon", "dept": "69", "pop": 520000},
        )
        cls.factory = APIRequestFactory()

    def make_request(self, path="/"):
        return Request(self.factory.get(path))

    def test_get_serializer_class(self):
        view = FeatureViewSet()
        view.kwargs = {}

        # 1. geometry param
        view.request = self.make_request("/?geometry=true")
        self.assertEqual(view.get_serializer_class(), FeatureGeoSerializer)

        # 2. all param
        view.request = self.make_request("/?all=true")
        self.assertEqual(view.get_serializer_class(), FeatureGeoSerializer)

        # 3. format="geojson"
        view.request = self.make_request("/")
        view.kwargs = {"format": "geojson"}
        self.assertEqual(view.get_serializer_class(), FeatureGeoSerializer)

        # 4. default
        view.kwargs = {}
        view.request = self.make_request("/")
        self.assertEqual(view.get_serializer_class(), FeatureListSerializer)

    def test_get_serializer_context(self):
        view = FeatureViewSet()
        view.format_kwarg = None
        view.kwargs = {"layer": str(self.layer.pk)}

        # 1. fields query param
        view.request = self.make_request("/?fields=name,pop")
        ctx = view.get_serializer_context()
        self.assertEqual(ctx["selected_fields"], ["name", "pop"])

        # 2. implicit filter fields
        view.request = self.make_request("/?name=Paris")
        ctx = view.get_serializer_context()
        self.assertEqual(ctx["selected_fields"], ["name"])

    def test_get_search_fields(self):
        view = FeatureViewSet()
        view.get_layer = mock.MagicMock()

        # layer with schema
        layer_with_schema = mock.MagicMock()
        layer_with_schema.schema = {"properties": {"name": {}, "pop": {}}}
        layer_with_schema.layer_properties = ["name", "pop"]
        view.get_layer.return_value = layer_with_schema
        self.assertEqual(
            view._get_search_fields(), ["properties__name", "properties__pop"]
        )

        # layer without schema with features
        view.get_layer.return_value = self.layer
        fields = view._get_search_fields()
        self.assertIn("properties__name", fields)

        # layer without schema and no features
        empty_layer = Layer.objects.create(name="empty_search_layer")
        view.get_layer.return_value = empty_layer
        self.assertEqual(view._get_search_fields(), [])

    def test_add_search_boost_annotations_empty(self):
        view = FeatureViewSet()
        view._get_search_fields = mock.MagicMock(return_value=[])
        qs = Feature.objects.filter(layer=self.layer)
        res_qs, parts = view._add_search_boost_annotations(qs, "search_term")
        self.assertEqual(parts, [])
        self.assertEqual(res_qs, qs)

    def test_strip_accents_and_inject_search_match(self):
        self.assertEqual(FeatureViewSet._strip_accents("Éléphant"), "Elephant")

        view = FeatureViewSet()
        # search_param empty -> no op
        features = [{"properties": {"name": "Toulouse"}}]
        view._inject_search_match(features, "")
        self.assertNotIn("search_match", features[0]["properties"])

        # match in properties
        view._inject_search_match(features, "toul")
        self.assertEqual(features[0]["properties"]["search_match"], "name")

    def test_format_feature_response_geojson_wrapping(self):
        view = FeatureViewSet()
        view.request = self.make_request("/?geometry=true")
        view.kwargs = {}
        data = [{"id": 1, "properties": {"name": "Paris"}}]
        formatted = view._format_feature_response(data, "par")
        self.assertEqual(formatted["type"], "FeatureCollection")
        self.assertEqual(formatted["features"][0]["properties"]["search_match"], "name")

    def test_list_action(self):
        view = FeatureViewSet.as_view({"get": "list"})

        # normal list
        req = self.factory.get(f"/api/geo-api/{self.layer.pk}/feature/")
        res = view(req, layer=str(self.layer.pk))
        self.assertEqual(res.status_code, 200)

        # list with search
        req = self.factory.get(f"/api/geo-api/{self.layer.pk}/feature/?search=toulouse")
        res = view(req, layer=str(self.layer.pk))
        self.assertEqual(res.status_code, 200)

        # list without pagination
        with mock.patch.object(FeatureViewSet, "paginate_queryset", return_value=None):
            req = self.factory.get(f"/api/geo-api/{self.layer.pk}/feature/")
            res = view(req, layer=str(self.layer.pk))
            self.assertEqual(res.status_code, 200)

    def test_distinct_and_distinct_all_actions(self):
        view_distinct = FeatureViewSet.as_view({"get": "distinct"})
        view_distinct_all = FeatureViewSet.as_view({"get": "distinct_all"})

        # distinct without q
        req = self.factory.get(f"/api/geo-api/{self.layer.pk}/feature/distinct/dept/")
        res = view_distinct(req, layer=str(self.layer.pk), field="dept")
        self.assertEqual(res.status_code, 200)

        # distinct with q
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/distinct/name/?q=tou"
        )
        res = view_distinct(req, layer=str(self.layer.pk), field="name")
        self.assertEqual(res.status_code, 200)

        # distinct without pagination
        with mock.patch.object(FeatureViewSet, "paginate_queryset", return_value=None):
            req = self.factory.get(
                f"/api/geo-api/{self.layer.pk}/feature/distinct/dept/"
            )
            res = view_distinct(req, layer=str(self.layer.pk), field="dept")
            self.assertEqual(res.status_code, 200)
            self.assertIn("31", res.data)

        # distinct_all
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/distinct/all/dept/"
        )
        res = view_distinct_all(req, layer=str(self.layer.pk), field="dept")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(set(res.data), {"31", "75", "69"})

    def test_extent_action(self):
        view = FeatureViewSet.as_view({"get": "extent"})

        # 1. extent without identifiers
        req = self.factory.get(f"/api/geo-api/{self.layer.pk}/feature/extent/")
        res = view(req, layer=str(self.layer.pk))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["bbox"]), 4)

        # 2. extent with specific identifiers
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/extent/?identifier=feat-tls,feat-prs"
        )
        res = view(req, layer=str(self.layer.pk))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["bbox"]), 4)

        # 3. empty layer extent -> 404
        empty_layer = Layer.objects.create(name="empty_extent_layer")
        req = self.factory.get(f"/api/geo-api/{empty_layer.pk}/feature/extent/")
        res = view(req, layer=str(empty_layer.pk))
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data["error"], "no data")

    def test_count_action(self):
        view = FeatureViewSet.as_view({"get": "count"})

        # count all
        req = self.factory.get(f"/api/geo-api/{self.layer.pk}/feature/count/")
        res = view(req, layer=str(self.layer.pk))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 3)

        # count with filter
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/count/?name=Paris"
        )
        res = view(req, layer=str(self.layer.pk))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
