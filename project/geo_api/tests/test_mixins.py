from django.test import TestCase
from geostore.models import Feature, Layer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from project.geo_api.mixins import AutoOrderMixin, PrefixBoostMixin


class DummyAutoOrderView(AutoOrderMixin):
    def __init__(self, request):
        self.request = request


class DummyPrefixBoostView(PrefixBoostMixin):
    def __init__(self, request):
        self.request = request


class MixinsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.layer = Layer.objects.create(name="mixins_layer")
        cls.factory = APIRequestFactory()

    def make_request(self, path="/"):
        return Request(self.factory.get(path))

    def test_auto_order_mixin(self):
        # 1. mix of op (>, <, invalid), range, and skip
        req = self.make_request("/?limit=10&pop>=1000&cost<50&bad_num>foo&height=10-20")
        view = DummyAutoOrderView(req)
        parts = view._collect_auto_order_parts()
        self.assertIn("_op_pop", parts)
        self.assertIn("-_op_cost", parts)
        self.assertIn("_op_height", parts)
        self.assertNotIn("_op_bad_num", parts)
        self.assertNotIn("limit", parts)

    def test_prefix_boost_mixin_with_ordering_specified(self):
        req = self.make_request("/?city=Paris&ordering=-pop")
        view = DummyPrefixBoostView(req)
        qs = Feature.objects.filter(layer=self.layer)
        res = view._apply_prefix_boost(qs)
        self.assertEqual(res, qs)

    def test_prefix_boost_mixin_with_text_filters(self):
        req = self.make_request("/?city=Paris")
        view = DummyPrefixBoostView(req)
        qs = Feature.objects.filter(layer=self.layer)
        # We need _una_city to exist or annotate it
        from project.geo_api.filters import NoAccentFilterBackend

        backend = NoAccentFilterBackend()
        qs = backend.filter_queryset(req, qs, view)

        res = view._apply_prefix_boost(qs, extra_order_parts=["identifier"])
        # Queryset should have order_by containing _boost_city, _una_city, identifier
        order_fields = list(res.query.order_by)
        self.assertIn("_boost_city", order_fields)
        self.assertIn("_una_city", order_fields)
        self.assertIn("identifier", order_fields)

    def test_prefix_boost_mixin_without_text_filters_and_no_extra(self):
        req = self.make_request("/?limit=10")
        view = DummyPrefixBoostView(req)
        qs = Feature.objects.filter(layer=self.layer)
        res = view._apply_prefix_boost(qs)
        self.assertEqual(res, qs)
