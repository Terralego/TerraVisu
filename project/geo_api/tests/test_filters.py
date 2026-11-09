from unittest import mock

from django.contrib.gis.geos import Point
from django.test import TestCase
from geostore.models import Feature, Layer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from project.geo_api.filters import (
    BBoxFilterBackend,
    NoAccentFilterBackend,
    OperatorFilterBackend,
    OrderingFilterBackend,
    PropertiesFilterBackend,
    SearchAllFieldsBackend,
    _classify_params,
    _clean_params,
)


class FiltersUnitTestCase(TestCase):
    def test_clean_params(self):
        self.assertEqual(list(_clean_params({"age>=10": ""})), [("age", ">=10")])
        self.assertEqual(list(_clean_params({"age<=15": ""})), [("age", "<=15")])
        self.assertEqual(list(_clean_params({"age>20": ""})), [("age", ">20")])
        self.assertEqual(list(_clean_params({"age<30": ""})), [("age", "<30")])
        self.assertEqual(list(_clean_params({"val<": "10"})), [("val", "<=10")])
        self.assertEqual(list(_clean_params({"val>": "10"})), [("val", ">=10")])
        self.assertEqual(list(_clean_params({"normal": "val"})), [("normal", "val")])
        self.assertEqual(list(_clean_params({"empty": ""})), [("empty", "")])

    def test_classify_params(self):
        params = {
            "limit": "10",
            "properties__something": "val",
            "cities": "Paris, Lyon, Marseille",
            "age": ">=18",
            "range_field": "10 - 25",
            "name": "Martin",
            "": "empty",
        }
        classified = list(_classify_params(params))
        cats = {cat for cat, key, *rest in classified}
        self.assertIn("skip", cats)
        self.assertIn("in", cats)
        self.assertIn("op", cats)
        self.assertIn("range", cats)
        self.assertIn("text", cats)

        # check in
        in_item = next(item for item in classified if item[0] == "in")
        self.assertEqual(in_item[1], "cities")
        self.assertEqual(in_item[2], ["Paris", "Lyon", "Marseille"])

        # check op
        op_item = next(item for item in classified if item[0] == "op")
        self.assertEqual(op_item[1], "age")
        self.assertEqual(op_item[2], ">=")
        self.assertEqual(op_item[3], "18")

        # check range
        range_item = next(item for item in classified if item[0] == "range")
        self.assertEqual(range_item[1], "range_field")
        self.assertEqual(range_item[2], 10.0)
        self.assertEqual(range_item[3], 25.0)

        # check text
        text_item = next(item for item in classified if item[0] == "text")
        self.assertEqual(text_item[1], "name")
        self.assertEqual(text_item[2], "Martin")


class FilterBackendsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.layer = Layer.objects.create(name="geo_layer")
        cls.f1 = Feature.objects.create(
            layer=cls.layer,
            geom=Point(1.44, 43.60),
            identifier="feat-toulouse",
            properties={"city": "Toulouse", "pop": 490000, "region": "Occitanie"},
        )
        cls.f2 = Feature.objects.create(
            layer=cls.layer,
            geom=Point(2.35, 48.85),
            identifier="feat-paris",
            properties={"city": "Paris", "pop": 2160000, "region": "Île-de-France"},
        )
        cls.f3 = Feature.objects.create(
            layer=cls.layer,
            geom=Point(4.83, 45.76),
            identifier="feat-lyon",
            properties={
                "city": "Lyon",
                "pop": 520000,
                "region": "Auvergne-Rhône-Alpes",
            },
        )
        cls.factory = APIRequestFactory()

    def make_request(self, path="/"):
        return Request(self.factory.get(path))

    def test_search_all_fields_backend(self):
        backend = SearchAllFieldsBackend()
        view = mock.MagicMock()
        view.get_layer.return_value = self.layer

        # 1. No search term
        req = self.make_request("/")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 3)

        # 2. Search without schema (uses first feature properties)
        req = self.make_request("/?search=toulouse")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().identifier, "feat-toulouse")

        # 3. Search with non-properties field (e.g. identifier)
        with mock.patch.object(
            backend, "get_search_fields", return_value=["identifier"]
        ):
            req = self.make_request("/?search=feat-paris")
            qs = backend.filter_queryset(
                req, Feature.objects.filter(layer=self.layer), view
            )
            self.assertEqual(qs.count(), 1)
            self.assertEqual(qs.first().identifier, "feat-paris")

        # 4. Search without fields
        with mock.patch.object(backend, "get_search_fields", return_value=[]):
            req = self.make_request("/?search=paris")
            qs = backend.filter_queryset(
                req, Feature.objects.filter(layer=self.layer), view
            )
            self.assertEqual(qs.count(), 3)

        # 5. Layer with no features returns []
        empty_layer = Layer.objects.create(name="empty_layer")
        view_empty = mock.MagicMock()
        view_empty.get_layer.return_value = empty_layer
        fields = backend.get_search_fields(view_empty, req)
        self.assertEqual(fields, [])

    def test_no_accent_filter_backend(self):
        backend = NoAccentFilterBackend()
        view = mock.MagicMock()

        # text filter with accent: "ile-de-france" matches "Île-de-France"
        req = self.make_request("/?region=ile-de-france")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().identifier, "feat-paris")

        # non-text parameter should be skipped by NoAccentFilterBackend
        req = self.make_request("/?pop>=1000000")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 3)

    def test_properties_filter_backend(self):
        backend = PropertiesFilterBackend()
        view = mock.MagicMock()

        # int filter
        req = self.make_request("/?properties__pop=490000")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().identifier, "feat-toulouse")

        # float filter
        req = self.make_request("/?properties__rate=12.5")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 0)

        # non-numeric string filter
        req = self.make_request("/?properties__city=Lyon")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)

        # ignored keys
        req = self.make_request("/?non_prop=123&properties__empty=")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 3)

    def test_operator_filter_backend(self):
        backend = OperatorFilterBackend()
        view = mock.MagicMock()

        # in operator
        req = self.make_request("/?city=Toulouse,Lyon")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 2)

        # op: >=
        req = self.make_request("/?pop>=520000")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 2)

        # op: >
        req = self.make_request("/?pop>520000")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().identifier, "feat-paris")

        # op: <=
        req = self.make_request("/?pop<=520000")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 2)

        # op: <
        req = self.make_request("/?pop<520000")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().identifier, "feat-toulouse")

        # op with invalid float
        req = self.make_request("/?pop>=not_a_number")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 3)

        # range: 500000 - 600000
        req = self.make_request("/?pop=500000-600000")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().identifier, "feat-lyon")

    def test_bbox_filter_backend(self):
        backend = BBoxFilterBackend()
        view = mock.MagicMock()

        # empty bbox
        req = self.make_request("/")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 3)

        # invalid bbox (letters)
        req = self.make_request("/?bbox=a,b,c,d")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 3)

        # invalid bbox (not 4 parts)
        req = self.make_request("/?bbox=1,2,3")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 3)

        # valid bbox around Toulouse (lng: 1.44, lat: 43.60)
        req = self.make_request("/?bbox=1.0,43.0,2.0,44.0")
        qs = backend.filter_queryset(
            req, Feature.objects.filter(layer=self.layer), view
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().identifier, "feat-toulouse")

    def test_ordering_filter_backend(self):
        from project.geo_api.views.feature_viewset import FeatureViewSet

        backend = OrderingFilterBackend()
        view = FeatureViewSet()
        view.get_layer = mock.MagicMock(return_value=self.layer)

        # layer without schema
        fields = backend.get_valid_fields(
            Feature.objects.filter(layer=self.layer), view
        )
        self.assertIsInstance(fields, list)

        # layer with schema
        self.layer.schema = {
            "properties": {
                "city": {"title": "City Name"},
                "pop": {"title": "Population"},
            }
        }
        self.layer.save()
        fields = backend.get_valid_fields(
            Feature.objects.filter(layer=self.layer), view
        )
        field_names = [f[0] for f in fields]
        self.assertIn("properties__city", field_names)
        self.assertIn("properties__pop", field_names)

        # remove_invalid_fields
        req = self.make_request("/?ordering=-pop,identifier")
        # "pop" is not a model name, should become "-properties__pop"
        # "identifier" is a model field on Feature
        cleaned = backend.remove_invalid_fields(
            Feature.objects.filter(layer=self.layer), ["-pop", "identifier"], view, req
        )
        self.assertEqual(cleaned, ["-properties__pop", "identifier"])

        # Test line 238: model field not in valid
        view.ordering_fields = ["id"]
        cleaned_model = backend.remove_invalid_fields(
            Feature.objects.filter(layer=self.layer), ["geom"], view, req
        )
        self.assertEqual(cleaned_model, ["geom"])
