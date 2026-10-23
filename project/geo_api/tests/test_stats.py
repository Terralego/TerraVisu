from unittest import mock

from django.contrib.gis.geos import Point
from geostore.models import Feature, Layer
from rest_framework.test import APIRequestFactory

from project.geo_api.views.feature_viewset import FeatureViewSet
from project.geo_api.views.stats import (
    ALL_STATS_FIELDS,
    _aggregate_stats,
    _cast_field,
    _compute_fd_bins,
    _count_by_intervals,
    _round_val,
)

from .base import BaseGeoAPITestCase


class StatsUnitTestCase(BaseGeoAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.layer = Layer.objects.create(name="stats_layer")
        for i in range(1, 11):
            Feature.objects.create(
                layer=cls.layer,
                geom=Point(float(i), float(i)),
                identifier=f"feat-{i}",
                properties={"val": i * 10, "val.keyword": f"{i * 10}"},
            )
        cls.factory = APIRequestFactory()

    def test_cast_field(self):
        expr = _cast_field("val.keyword")
        self.assertIsNotNone(expr)

    def test_round_val(self):
        self.assertEqual(_round_val(12.3456), 12.35)
        self.assertIsNone(_round_val(None))
        self.assertEqual(_round_val("not_a_number"), "not_a_number")

    def test_count_by_intervals(self):
        qs = Feature.objects.filter(layer=self.layer)
        cast_f = _cast_field("val")
        # Empty intervals
        self.assertEqual(_count_by_intervals(qs, cast_f, []), [])

        # Multiple intervals: [10, 30], [30, 60], [60, 100]
        intervals = [(10, 30), (30, 60), (60, 100)]
        counts = _count_by_intervals(qs, cast_f, intervals)
        # val=10, 20 in first; 30, 40, 50 in second; 60, 70, 80, 90, 100 in third
        self.assertEqual(counts, [2, 3, 5])

    def test_aggregate_stats(self):
        qs = Feature.objects.filter(layer=self.layer)
        cast_f = _cast_field("val")

        # Empty fields
        self.assertEqual(_aggregate_stats(qs, cast_f, fields=set()), {})

        # Default fields (line 86)
        default_res = _aggregate_stats(qs, cast_f)
        self.assertEqual(default_res["min"], 10.0)
        self.assertEqual(default_res["max"], 100.0)

        # All fields
        res = _aggregate_stats(qs, cast_f, fields=ALL_STATS_FIELDS)
        self.assertEqual(res["min"], 10.0)
        self.assertEqual(res["max"], 100.0)
        self.assertEqual(res["count"], 10)
        self.assertEqual(res["total_count"], 10)
        self.assertEqual(res["sum"], 550.0)
        self.assertEqual(res["avg"], 55.0)
        self.assertIsNotNone(res["std_dev"])
        self.assertEqual(res["median"], 55.0)

    def test_compute_fd_bins(self):
        qs = Feature.objects.filter(layer=self.layer)

        # count is None (line 120)
        bins_no_count = _compute_fd_bins(qs, "val", 10, 100, 30, 70)
        self.assertTrue(len(bins_no_count) > 0)

        # count < 2 or min == max
        bins = _compute_fd_bins(qs, "val", 10, 10, 10, 10, count=1)
        self.assertEqual(len(bins), 1)
        self.assertEqual(bins[0]["count"], 1)

        # iqr == 0
        bins_zero_iqr = _compute_fd_bins(qs, "val", 0, 100, 50, 50, count=10)
        self.assertTrue(len(bins_zero_iqr) > 0)

        # bin_width <= 0 (line 132)
        bins_negative_width = _compute_fd_bins(qs, "val", 10, 100, 80, 20, count=10)
        self.assertTrue(len(bins_negative_width) > 0)

        # normal iqr
        bins_normal = _compute_fd_bins(qs, "val", 10, 100, 32.5, 77.5, count=10)
        self.assertTrue(len(bins_normal) > 0)

        # clamped > 100 bins
        bins_clamped = _compute_fd_bins(qs, "val", 0, 1000, 100, 100.001, count=10)
        self.assertLessEqual(len(bins_clamped), 100)

    def test_stats_action(self):
        view = FeatureViewSet.as_view({"get": "stats"})
        req = self.factory.get(f"/api/geo-api/{self.layer.pk}/feature/stats/val/")
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["min"], 10.0)
        self.assertEqual(res.data["max"], 100.0)

    def test_distribution_action_with_data(self):
        view = FeatureViewSet.as_view({"get": "distribution"})
        req = self.factory.get(
            f"/api/geo-api/{self.layer.pk}/feature/stats/val/distribution/"
        )
        res = view(req, layer=str(self.layer.pk), field="val")
        self.assertEqual(res.status_code, 200)
        self.assertIn("bins", res.data)
        self.assertIn("boxplot", res.data)
        self.assertIn("sample", res.data)
        self.assertEqual(res.data["boxplot"]["min"], 10.0)
        self.assertEqual(res.data["boxplot"]["max"], 100.0)
        self.assertEqual(len(res.data["sample"]), 10)

    def test_distribution_action_empty_layer(self):
        empty_layer = Layer.objects.create(name="empty_stats_layer")
        view = FeatureViewSet.as_view({"get": "distribution"})
        req = self.factory.get(
            f"/api/geo-api/{empty_layer.pk}/feature/stats/val/distribution/"
        )
        res = view(req, layer=str(empty_layer.pk), field="val")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"bins": [], "boxplot": {}, "sample": []})

    def test_distribution_action_large_sample(self):
        view = FeatureViewSet()
        view.get_layer = mock.MagicMock(return_value=self.layer)
        req = self.factory.get("/")
        with mock.patch("project.geo_api.views.stats._aggregate_stats") as mock_agg:
            mock_agg.return_value = {
                "min": 1,
                "max": 100,
                "q1": 25,
                "q3": 75,
                "median": 50,
                "count": 2000,
            }
            with mock.patch(
                "project.geo_api.views.stats._compute_fd_bins", return_value=[]
            ):
                res = view.distribution(req, layer=str(self.layer.pk), field="val")
                self.assertEqual(res.status_code, 200)
