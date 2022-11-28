import random

from django.contrib.gis.geos import Point
from django.test import TestCase
from geostore.models import Feature

from project.geosource.models import PostGISSource
from project.terra_layer.models import CustomStyle, Layer
from project.terra_layer.style.utils import (
    ceil_scale,
    circle_boundaries_candidate,
    circle_boundaries_filter_values,
    get_min_max,
    round_scale,
    trunc_scale,
)


class StyleTestCase(TestCase):
    def setUp(self):
        self.source = PostGISSource.objects.create(
            name="test",
            db_name="test",
            db_password="test",
            db_host="localhost",
            geom_type=1,
            refresh=-1,
        )
        self.layer = Layer.objects.create(
            source=self.source,
            name="my_layer_name",
            uuid="91c60192-9060-4bf6-b0de-818c5a362d89",
        )
        self.maxDiff = None

    def _feature_factory(self, geo_layer, **properties):
        return Feature.objects.create(
            layer=geo_layer,
            geom=Point(-1.560408, 47.218658),
            properties=properties,
        )

    def test_get_min_max(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.assertEqual(get_min_max(geo_layer, "a"), [False, 1.0, 2.0])

    def test_get_positive_min_max(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.assertEqual(get_min_max(geo_layer, "a"), [False, 1.0, 2.0])

    def test_get_no_positive_min_max(self):
        geo_layer = self.source.get_layer()
        self.assertEqual(get_min_max(geo_layer, "a"), [False, None, None])

    def test_get_no_min_max(self):
        geo_layer = self.source.get_layer()
        self.assertEqual(get_min_max(geo_layer, "a"), [False, None, None])

    def test_circle_boundaries_0(self):
        min = 0
        max = 1
        with self.assertRaises(ValueError):
            circle_boundaries_candidate(min, max)

    def test_circle_boundaries_1(self):
        min = 1
        max = 1
        size = 100
        candidates = circle_boundaries_candidate(min, max)
        candidates = [max] + candidates + [min]
        boundaries = circle_boundaries_filter_values(candidates, min, max, size / 20)
        self.assertEqual(boundaries, [1])

    def test_circle_boundaries_100(self):
        min = 1
        max = 100
        size = 100
        candidates = circle_boundaries_candidate(min, max)
        candidates = [max] + candidates + [min]
        boundaries = circle_boundaries_filter_values(candidates, min, max, size / 20)
        self.assertEqual(boundaries, [100, 50, 25, 10, 5, 2.5])

    def test_circle_boundaries_001(self):
        min = 0.001
        max = 0.1
        size = 100
        candidates = circle_boundaries_candidate(min, max)
        candidates = [max] + candidates + [min]
        boundaries = circle_boundaries_filter_values(candidates, min, max, size / 20)
        # Stange
        self.assertEqual(boundaries, [0.1])
        # Should be
        # self.assertEqual(boundaries, [.1, .05, .025, .001, .0005, .00025])

    def test_circle_boundaries_none(self):
        min = None
        max = None
        size = 100
        candidates = circle_boundaries_candidate(min, max)
        candidates = [max] + candidates + [min]
        boundaries = circle_boundaries_filter_values(candidates, min, max, size / 20)
        self.assertEqual(boundaries, [])

    def test_round_scale(self):
        self.assertEqual(trunc_scale(0, 3), 0)

        self.assertEqual(trunc_scale(111, 3), 111)
        self.assertEqual(trunc_scale(111, 2), 110)
        self.assertEqual(trunc_scale(111, 1), 100)

        self.assertEqual(round_scale(111, 3), 111)
        self.assertEqual(round_scale(111, 2), 110)
        self.assertEqual(round_scale(111, 1), 100)

        self.assertEqual(round_scale(117, 3), 117)
        self.assertEqual(round_scale(117, 2), 120)
        self.assertEqual(round_scale(117, 1), 100)

        self.assertEqual(ceil_scale(117, 3), 117)
        self.assertEqual(ceil_scale(117, 2), 120)
        self.assertEqual(ceil_scale(117, 1), 200)

        self.assertEqual(trunc_scale(0.51, 3), 0.51)
        self.assertEqual(trunc_scale(0.51, 2), 0.5)
        self.assertEqual(trunc_scale(0.51, 1), 0)

        self.assertEqual(round_scale(0.51, 3), 0.51)
        self.assertEqual(round_scale(0.51, 2), 0.5)
        self.assertEqual(round_scale(0.51, 1), 1)

        self.assertEqual(round_scale(0.49, 3), 0.49)
        self.assertEqual(round_scale(0.49, 2), 0.5)
        self.assertEqual(round_scale(0.49, 1), 0)

        self.assertEqual(ceil_scale(0.58, 3), 0.58)
        self.assertEqual(
            ceil_scale(0.58, 2), 0.6000000000000001
        )  # Got it, exactly what I want
        self.assertEqual(ceil_scale(0.58, 1), 1)

    def test_analysis_fail(self):
        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "fill",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "method": "jenks",
                    "analysis": "__666__",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        with self.assertRaises(ValueError):
            self.layer.save()

    def test_method_fail(self):
        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "fill",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "method": "__666__",
                    "analysis": "graduated",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        with self.assertRaises(ValueError):
            self.layer.save()

    def test_empty(self):
        geo_layer = self.source.get_layer()
        geo_layer.main_style = {}
        geo_layer.save()

        # Make a random change on the layer before save
        self.layer.name = "foobar"
        self.layer.save()
        self.assertEqual(self.layer.main_style, {})
        self.assertEqual(self.layer.legends, [])

    def test_no_wizard(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),

        self.layer.main_style = {}
        self.layer.save()

        self.assertEqual(self.layer.main_style, {})
        self.assertEqual(self.layer.legends, [])

    def test_0graduated_equal_interval(self):
        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "equal_interval",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "paint": {"fill-color": "#aa0000", "fill-outline-color": "#ffffff"},
                "type": "fill",
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "title": "my_layer_name",
                }
            ],
        )

    def test_0graduated_quantile(self):
        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "quantile",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "paint": {"fill-color": "#aa0000", "fill-outline-color": "#ffffff"},
                "type": "fill",
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "title": "my_layer_name",
                }
            ],
        )

    def test_0graduated_jenks(self):
        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "jenks",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "paint": {"fill-color": "#aa0000", "fill-outline-color": "#ffffff"},
                "type": "fill",
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "title": "my_layer_name",
                }
            ],
        )

    def test_update_wizard(self):
        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "fill",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "method": "jenks",
                    "analysis": "graduated",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "paint": {"fill-color": "#aa0000", "fill-outline-color": "#ffffff"},
                "type": "fill",
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "title": "my_layer_name",
                }
            ],
        )

        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "fill",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "b",
                    "method": "jenks",
                    "analysis": "graduated",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "paint": {"fill-color": "#aa0000", "fill-outline-color": "#ffffff"},
                "type": "fill",
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "title": "my_layer_name",
                }
            ],
        )

    def test_update_wizard_for_extra_style(self):
        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "fill",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        CustomStyle.objects.create(
            style_config={
                "type": "wizard",
                "map_style_type": "fill",
                "uid": "f4bd8a48-3715-4ea0-ae02-b1d827bcb599",
                "style": {
                    "fill_color": {
                        "type": "variable",
                        "field": "a",
                        "method": "jenks",
                        "analysis": "graduated",
                        "values": ["#aa0000", "#770000", "#330000", "#000000"],
                        "generate_legend": True,
                    },
                },
            },
            source=self.layer.source,
            layer=self.layer,
        )

        self.layer.save()

        self.assertEqual(
            self.layer.extra_styles.first().style_config["map_style"],
            {
                "paint": {"fill-color": "#aa0000"},
                "type": "fill",
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "uid": "f4bd8a48-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "title": "my_layer_name",
                    "shape": "square",
                    "auto": True,
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                }
            ],
        )

    def test_update_wizard_for_extra_style_update(self):
        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "fill",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        custom = CustomStyle.objects.create(
            style_config={
                "type": "wizard",
                "map_style_type": "fill",
                "uid": "f4bd8a48-3715-4ea0-ae02-b1d827bcb599",
                "style": {
                    "fill_color": {
                        "type": "variable",
                        "field": "a",
                        "method": "jenks",
                        "analysis": "graduated",
                        "values": ["#aa0000", "#770000", "#330000", "#000000"],
                        "generate_legend": True,
                    },
                    "fill_outline_color": {
                        "type": "variable",
                        "field": "a",
                        "analysis": "graduated",
                        "method": "jenks",
                        "values": ["#aa0000", "#770000", "#330000", "#000000"],
                        "generate_legend": True,
                    },
                },
            },
            source=self.layer.source,
            layer=self.layer,
        )

        self.layer.save()

        self.assertEqual(len(self.layer.legends), 2)

        self.layer.legends[0]["title"] = "Another title"
        self.layer.main_style["style"] = {
            "fill_color": {
                "type": "variable",
                "field": "a",
                "method": "jenks",
                "analysis": "graduated",
                "values": ["#aa0000", "#770000", "#330000", "#000000"],
                "generate_legend": True,
            },
        }

        custom.style_config["style"] = {
            "fill_color": {
                "type": "variable",
                "field": "a",
                "method": "jenks",
                "analysis": "graduated",
                "values": ["#cc0000", "#bb0000", "#330000", "#000000"],
                "generate_legend": True,
            },
        }
        custom.save()

        self.layer.legends.insert(
            0,
            {
                "items": [
                    {
                        "color": "#aa0000",
                        "boundaries": {
                            "lower": {"value": None, "included": True},
                            "upper": {"value": None, "included": True},
                        },
                    }
                ],
                "shape": "square",
                "title": "Manual legend",
            },
        )

        self.layer.save()

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "title": "Manual legend",
                },
                {
                    "items": [
                        {
                            "color": "#cc0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "uid": "f4bd8a48-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "title": "Another title",
                    "auto": True,
                },
                {
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "title": "my_layer_name",
                    "auto": True,
                },
            ],
        )

    def test_update_wizard_only_for_good_style(self):
        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "fill",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "method": "jenks",
                    "analysis": "graduated",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
                "line_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "paint": {"fill-color": "#aa0000", "fill-outline-color": "#ffffff"},
                "type": "fill",
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "shape": "square",
                    "title": "my_layer_name",
                }
            ],
        )

    def test_bad_analysis(self):
        self.source.get_layer()

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "___666___",
                },
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

        self.layer.main_style = {
            "map_style_type": "circle",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "circle_radius": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "___666___",
                },
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

        self.layer.main_style = {
            "map_style_type": "line",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "___666___",
                },
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

    def test_no_method_nor_boundaries(self):
        self.source.get_layer()

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                },
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

        self.layer.main_style = {
            "map_style_type": "line",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "values": [10, 20, 30, 40],
                },
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

    def test_boundaries_less(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "boundaries": [],
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

    def test_boundaries_1(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "boundaries": [0],
                    "analysis": "graduated",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

        self.layer.main_style = {
            "map_style_type": "line",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "boundaries": [0],
                    "values": [10, 20, 30, 40],
                    "generate_legend": True,
                },
            },
        }
        with self.assertRaises(ValueError):
            self.layer.save()

    def test_boundaries_no_value(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "b",
                    "analysis": "graduated",
                    "method": "quantile",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "no_value": "#000000",
                    "generate_legend": True,
                },
                "fill_opacity": {
                    "type": "fixed",
                    "value": 0.4,
                    "field": "b",
                    "no_value": 0,
                },
                "fill_outline_color": {
                    "type": "fixed",
                    "value": "#ffffff",
                },
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": "#000000",
                    "fill-opacity": [
                        "case",
                        ["==", ["typeof", ["get", "b"]], "number"],
                        0.4,
                        0,
                    ],
                    "fill-outline-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "title": "my_layer_name",
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                }
            ],
        )

    def test_boundaries(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "boundaries": [0, 10, 20, 30, 40],
                    "analysis": "graduated",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "step",
                        ["get", "a"],
                        "#aa0000",
                        10,
                        "#770000",
                        20,
                        "#330000",
                        30,
                        "#000000",
                    ],
                    "fill-outline-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": 30, "included": True},
                                "upper": {"value": 40, "included": True},
                            },
                        },
                        {
                            "color": "#330000",
                            "boundaries": {
                                "lower": {"value": 20, "included": True},
                                "upper": {"value": 30, "included": False},
                            },
                        },
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {"value": 10, "included": True},
                                "upper": {"value": 20, "included": False},
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": 0, "included": True},
                                "upper": {"value": 10, "included": False},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_boundaries_with_size(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "line",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "boundaries": [0, 10, 20, 30, 40],
                    "values": [10, 20, 30, 40],
                    "analysis": "graduated",
                    "generate_legend": True,
                    "no_value": 5,
                },
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "line",
                "paint": {
                    "line-width": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        ["step", ["get", "a"], 10, 10, 20, 20, 30, 30, 40],
                        5,
                    ]
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "line",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__line_width",
                    "items": [
                        {
                            "color": "#000000",
                            "strokeWidth": 40,
                            "boundaries": {
                                "lower": {"value": 30, "included": True},
                                "upper": {"value": 40, "included": True},
                            },
                        },
                        {
                            "color": "#000000",
                            "strokeWidth": 30,
                            "boundaries": {
                                "lower": {"value": 20, "included": True},
                                "upper": {"value": 30, "included": False},
                            },
                        },
                        {
                            "color": "#000000",
                            "strokeWidth": 20,
                            "boundaries": {
                                "lower": {"value": 10, "included": True},
                                "upper": {"value": 20, "included": False},
                            },
                        },
                        {
                            "color": "#000000",
                            "strokeWidth": 10,
                            "boundaries": {
                                "lower": {"value": 0, "included": True},
                                "upper": {"value": 10, "included": False},
                            },
                        },
                        {
                            "color": "#000000",
                            "strokeWidth": 5,
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_boundaries_null_value(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),
        self._feature_factory(geo_layer, a=None),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "boundaries": [0, 10, 20, 30, 40],
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "no_value": "#000000",
                    "generate_legend": True,
                },
                "fill_opacity": {
                    "type": "fixed",
                    "value": 0.4,
                },
                "fill_outline_color": {
                    "type": "fixed",
                    "value": "#fffffa",
                    "field": "a",
                    "no_value": "#ffffff",
                },
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        [
                            "step",
                            ["get", "a"],
                            "#aa0000",
                            10,
                            "#770000",
                            20,
                            "#330000",
                            30,
                            "#000000",
                        ],
                        "#000000",
                    ],
                    "fill-opacity": 0.4,
                    "fill-outline-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        "#fffffa",
                        "#ffffff",
                    ],
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": 30, "included": True},
                                "upper": {"value": 40, "included": True},
                            },
                        },
                        {
                            "color": "#330000",
                            "boundaries": {
                                "lower": {"value": 20, "included": True},
                                "upper": {"value": 30, "included": False},
                            },
                        },
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {"value": 10, "included": True},
                                "upper": {"value": 20, "included": False},
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": 0, "included": True},
                                "upper": {"value": 10, "included": False},
                            },
                        },
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_2equal_interval(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "equal_interval",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "step",
                        ["get", "a"],
                        "#aa0000",
                        1.25,
                        "#770000",
                        1.5,
                        "#330000",
                        1.75,
                        "#000000",
                    ],
                    "fill-outline-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": 1.75, "included": True},
                                "upper": {"value": 2.0, "included": True},
                            },
                        },
                        {
                            "color": "#330000",
                            "boundaries": {
                                "lower": {"value": 1.5, "included": True},
                                "upper": {"value": 1.75, "included": False},
                            },
                        },
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {"value": 1.25, "included": True},
                                "upper": {"value": 1.5, "included": False},
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": 1.0, "included": True},
                                "upper": {"value": 1.25, "included": False},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_2jenks(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "jenks",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "step",
                        ["get", "a"],
                        "#aa0000",
                        2.0,
                        "#770000",
                        2.0,
                        "#330000",
                    ],
                    "fill-outline-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {"value": 2.0, "included": True},
                                "upper": {"value": 2.0, "included": True},
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": 1.0, "included": True},
                                "upper": {"value": 2.0, "included": False},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_2quantile(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=1),
        self._feature_factory(geo_layer, a=2),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "quantile",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "step",
                        ["get", "a"],
                        "#aa0000",
                        2,
                        "#770000",
                        2,
                        "#330000",
                    ],
                    "fill-outline-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {"value": 2.0, "included": True},
                                "upper": {"value": 2.0, "included": True},
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {"value": 1.0, "included": True},
                                "upper": {"value": 2.0, "included": False},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_0circle(self):
        self.layer.main_style = {
            "map_style_type": "circle",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "circle_radius": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "proportionnal",
                    "max_radius": 200,
                    "generate_legend": True,
                    "no_value": 20,
                },
                "circle_color": {"type": "fixed", "value": "#0000cc"},
                "circle_stroke_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "layout": {"circle-sort-key": ["-", ["get", "a"]]},
                "paint": {
                    "circle-color": "#0000cc",
                    "circle-radius": 20,
                    "circle-stroke-color": "#ffffff",
                },
                "type": "circle",
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "title": "my_layer_name",
                    "auto": True,
                    "shape": "stackedCircle",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__circle_radius",
                    "items": [
                        {
                            "size": 20,
                            "color": "#0000cc",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                }
            ],
        )

    def test_2circle(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=0)
        self._feature_factory(geo_layer, a=1)
        self._feature_factory(geo_layer, a=129)

        self.maxDiff = None

        self.layer.main_style = {
            "map_style_type": "circle",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "circle_radius": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "proportionnal",
                    "max_radius": 200,
                    "generate_legend": True,
                },
                "circle_color": {"type": "fixed", "value": "#0000cc"},
                "circle_opacity": {"type": "fixed", "value": 0.4},
                "circle_stroke_color": {"type": "fixed", "value": "#ffffff"},
                "circle_stroke_width": {"type": "fixed", "value": 0.3},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "circle",
                "paint": {
                    "circle-radius": [
                        "interpolate",
                        ["linear"],
                        ["sqrt", ["/", ["get", "a"], ["pi"]]],
                        0,
                        0,
                        6.432750982580687,
                        100.0,
                    ],
                    "circle-color": "#0000cc",
                    "circle-opacity": 0.4,
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 0.3,
                },
                "layout": {"circle-sort-key": ["-", ["get", "a"]]},
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "stackedCircle",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__circle_radius",
                    "items": [
                        {
                            "size": 200.0,
                            "boundaries": {"lower": {"value": 130}},
                            "color": "#0000cc",
                        },
                        {
                            "size": 175.41160386140584,
                            "boundaries": {"lower": {"value": 100}},
                            "color": "#0000cc",
                        },
                        {
                            "size": 124.03473458920845,
                            "boundaries": {"lower": {"value": 50}},
                            "color": "#0000cc",
                        },
                        {
                            "size": 87.70580193070292,
                            "boundaries": {"lower": {"value": 25.0}},
                            "color": "#0000cc",
                        },
                        {
                            "size": 55.47001962252292,
                            "boundaries": {"lower": {"value": 10}},
                            "color": "#0000cc",
                        },
                        {
                            "size": 39.22322702763681,
                            "boundaries": {"lower": {"value": 5}},
                            "color": "#0000cc",
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_2circle_no_value(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=0)
        self._feature_factory(geo_layer, a=1)
        self._feature_factory(geo_layer, a=129)
        self.maxDiff = None

        self.layer.main_style = {
            "map_style_type": "circle",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "circle_radius": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "proportionnal",
                    "max_radius": 200,
                    "generate_legend": True,
                    "no_value": 30,
                },
                "circle_color": {
                    "type": "fixed",
                    "value": "#0000ca",
                    "field": "a",
                    "no_value": "#000000",
                },
                "circle_opacity": {
                    "type": "fixed",
                    "value": 0.4,
                    "field": "a",
                    "no_value": "#000000",
                },
                "circle_stroke_color": {
                    "type": "fixed",
                    "value": "#fffffa",
                    "field": "a",
                    "no_value": "#ffffff",
                },
                "circle_stroke_width": {
                    "type": "fixed",
                    "value": 0.3,
                    "field": "a",
                    "no_value": 0.2,
                },
            },
        }
        self.layer.save()

        interpolate = [
            "interpolate",
            ["linear"],
            ["sqrt", ["/", ["get", "a"], ["pi"]]],
            0,
            0,
            6.432750982580687,
            100.0,
        ]

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "circle",
                "paint": {
                    "circle-radius": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        interpolate,
                        30,
                    ],
                    "circle-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        "#0000ca",
                        "#000000",
                    ],
                    "circle-opacity": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        0.4,
                        "#000000",
                    ],
                    "circle-stroke-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        "#fffffa",
                        "#ffffff",
                    ],
                    "circle-stroke-width": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        0.3,
                        0.2,
                    ],
                },
                "layout": {"circle-sort-key": ["-", ["get", "a"]]},
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "stackedCircle",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__circle_radius",
                    "items": [
                        {
                            "size": 200.0,
                            "boundaries": {"lower": {"value": 130}},
                            "color": "#0000ca",
                        },
                        {
                            "size": 175.41160386140584,
                            "boundaries": {"lower": {"value": 100}},
                            "color": "#0000ca",
                        },
                        {
                            "size": 124.03473458920845,
                            "boundaries": {"lower": {"value": 50}},
                            "color": "#0000ca",
                        },
                        {
                            "size": 87.70580193070292,
                            "boundaries": {"lower": {"value": 25}},
                            "color": "#0000ca",
                        },
                        {
                            "size": 55.47001962252292,
                            "boundaries": {"lower": {"value": 10}},
                            "color": "#0000ca",
                        },
                        {
                            "size": 39.22322702763681,
                            "boundaries": {"lower": {"value": 5}},
                            "color": "#0000ca",
                        },
                        {
                            "size": 60,
                            "boundaries": {"lower": {"value": None}},
                            "color": "#000000",
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_nlines(self):
        geo_layer = self.source.get_layer()
        for a in [106.8, 59.2, 49.4, 0.1, 0]:
            self._feature_factory(geo_layer, a=a)

        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "line",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "proportionnal",
                    "max_value": 200,
                    "generate_legend": True,
                },
                "line_color": {"type": "fixed", "value": "#0000cc"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "line",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__line_width",
                    "items": [
                        {
                            "strokeWidth": 200.0,
                            "boundaries": {"lower": {"value": 110}},
                            "color": "#0000cc",
                        },
                        {
                            "strokeWidth": 99.0909090909091,
                            "boundaries": {"lower": {"value": 54.5}},
                            "color": "#0000cc",
                        },
                        {
                            "strokeWidth": 1.8181818181818181,
                            "boundaries": {"lower": {"value": 1}},
                            "color": "#0000cc",
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_nlines_w_default(self):
        geo_layer = self.source.get_layer()
        for a in [106.8, 59.2, 49.4, 0.1, 0]:
            self._feature_factory(geo_layer, a=a)

        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "line",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "proportionnal",
                    "max_value": 200,
                    "generate_legend": True,
                    "no_value": 10,
                },
                "line_color": {
                    "type": "fixed",
                    "value": "#0000cc",
                    "no_value": "#101010",
                },
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "line",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__line_width",
                    "items": [
                        {
                            "strokeWidth": 200.0,
                            "boundaries": {"lower": {"value": 110}},
                            "color": "#0000cc",
                        },
                        {
                            "strokeWidth": 99.0909090909091,
                            "boundaries": {"lower": {"value": 54.5}},
                            "color": "#0000cc",
                        },
                        {
                            "strokeWidth": 1.8181818181818181,
                            "boundaries": {"lower": {"value": 1}},
                            "color": "#0000cc",
                        },
                        {
                            "strokeWidth": 10,
                            "boundaries": {"lower": {"value": None}},
                            "color": "#101010",
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_nlines_only_none(self):
        geo_layer = self.source.get_layer()
        self._feature_factory(geo_layer, a=None)

        self.layer.main_style = {
            "type": "wizard",
            "map_style_type": "line",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "proportionnal",
                    "max_value": 200,
                    "generate_legend": True,
                },
                "line_color": {"type": "fixed", "value": "#0000cc"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "line",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__line_width",
                    "items": [
                        {
                            "strokeWidth": None,
                            "color": "#0000cc",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        }
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_gauss_graduated_equal_interval(self):
        geo_layer = self.source.get_layer()

        random.seed(33)
        for _ in range(0, 1000):
            self._feature_factory(geo_layer, a=random.gauss(0, 5)),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "equal_interval",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "step",
                        ["get", "a"],
                        "#aa0000",
                        -7.851838934271116,
                        "#770000",
                        -0.14888551711502096,
                        "#330000",
                        7.554067900041074,
                        "#000000",
                    ],
                    "fill-outline-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": 7.554067900041074, "included": True},
                                "upper": {"value": 15.25702131719717, "included": True},
                            },
                        },
                        {
                            "color": "#330000",
                            "boundaries": {
                                "lower": {
                                    "value": -0.14888551711502096,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 7.554067900041074,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {
                                    "value": -7.851838934271116,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -0.14888551711502096,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {
                                    "value": -15.554792351427212,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -7.851838934271116,
                                    "included": False,
                                },
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_gauss_graduated_quantile(self):
        geo_layer = self.source.get_layer()

        random.seed(33)
        for index in range(0, 1000):
            self._feature_factory(geo_layer, a=random.gauss(0, 5)),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "quantile",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#ffffff"},
            },
        }

        self.layer.save()
        self.maxDiff = None

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "step",
                        ["get", "a"],
                        "#aa0000",
                        -3.3519812305068184,
                        "#770000",
                        -0.011475353898097245,
                        "#330000",
                        3.186540376312785,
                        "#000000",
                    ],
                    "fill-outline-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": 3.186540376312785, "included": True},
                                "upper": {
                                    "value": 15.25702131719717,
                                    "included": True,
                                },
                            },
                        },
                        {
                            "color": "#330000",
                            "boundaries": {
                                "lower": {
                                    "value": -0.011475353898097245,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 3.186540376312785,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {
                                    "value": -3.3519812305068184,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -0.011475353898097245,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {
                                    "value": -15.554792351427212,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -3.3519812305068184,
                                    "included": False,
                                },
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_gauss_graduated_quantile_white_none(self):
        geo_layer = self.source.get_layer()

        random.seed(33)
        for index in range(0, 1000):
            self._feature_factory(geo_layer, a=random.gauss(0, 5)),
        for index in range(0, 10):
            self._feature_factory(geo_layer, a=None),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "quantile",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "no_value": "#000000",
                    "generate_legend": True,
                },
                "fill_opacity": {
                    "type": "fixed",
                    "value": 0.4,
                    "no_value": 0,
                    "field": "a",
                },
                "fill_outline_color": {
                    "type": "fixed",
                    "value": "#ffffff",
                    "no_value": "#ffffff",
                    "field": "a",
                },
            },
        }
        self.layer.save()
        self.maxDiff = None

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        [
                            "step",
                            ["get", "a"],
                            "#aa0000",
                            -3.307794810850208,
                            "#770000",
                            0.020384992547665716,
                            "#330000",
                            3.256429352130346,
                            "#000000",
                        ],
                        "#000000",
                    ],
                    "fill-opacity": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        0.4,
                        0,
                    ],
                    "fill-outline-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        "#ffffff",
                        "#ffffff",
                    ],
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": 3.256429352130346, "included": True},
                                "upper": {
                                    "value": 15.25702131719717,
                                    "included": True,
                                },
                            },
                        },
                        {
                            "color": "#330000",
                            "boundaries": {
                                "lower": {
                                    "value": 0.020384992547665716,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 3.256429352130346,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {
                                    "value": -3.307794810850208,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 0.020384992547665716,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {
                                    "value": -15.554792351427212,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -3.307794810850208,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_gauss_graduated_jenks(self):
        geo_layer = self.source.get_layer()

        random.seed(33)
        for index in range(0, 1000):
            self._feature_factory(geo_layer, a=random.gauss(0, 5)),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_outline_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "jenks",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "generate_legend": True,
                },
                "fill_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-outline-color": [
                        "step",
                        ["get", "a"],
                        "#aa0000",
                        -4.292341999003442,
                        "#770000",
                        0.5740581144424383,
                        "#330000",
                        5.727211814984125,
                        "#000000",
                    ],
                    "fill-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_outline_color",
                    "items": [
                        {
                            "strokeColor": "#000000",
                            "boundaries": {
                                "lower": {"value": 5.727211814984125, "included": True},
                                "upper": {
                                    "value": 15.25702131719717,
                                    "included": True,
                                },
                            },
                        },
                        {
                            "strokeColor": "#330000",
                            "boundaries": {
                                "lower": {
                                    "value": 0.5740581144424383,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 5.727211814984125,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "strokeColor": "#770000",
                            "boundaries": {
                                "lower": {
                                    "value": -4.292341999003442,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 0.5740581144424383,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "strokeColor": "#aa0000",
                            "boundaries": {
                                "lower": {
                                    "value": -15.554792351427212,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -4.292341999003442,
                                    "included": False,
                                },
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_graduated_jenks_only_none(self):
        geo_layer = self.source.get_layer()

        self._feature_factory(geo_layer, a=None),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "jenks",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "no_value": "#CC0000",
                    "generate_legend": True,
                },
                "fill_opacity": {
                    "type": "fixed",
                    "value": 0.4,
                    "field": "a",
                    "no_value": 0.5,
                },
                "fill_outline_color": {
                    "type": "fixed",
                    "value": "#ffffff",
                    "field": "a",
                    "no_value": "#00ffff",
                },
            },
        }

        self.layer.save()
        self.maxDiff = None

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": "#CC0000",
                    "fill-opacity": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        0.4,
                        0.5,
                    ],
                    "fill-outline-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        "#ffffff",
                        "#00ffff",
                    ],
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#CC0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_gauss_graduated_jenks_with_none(self):
        geo_layer = self.source.get_layer()

        random.seed(33)
        for index in range(0, 1000):
            self._feature_factory(geo_layer, a=random.gauss(0, 5)),
        for index in range(0, 10):
            self._feature_factory(geo_layer, a=None),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "jenks",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "no_value": "#CC0000",
                    "generate_legend": True,
                },
                "fill_opacity": {
                    "type": "fixed",
                    "value": 0.4,
                    "field": "a",
                    "no_value": 0.5,
                },
                "fill_outline_color": {
                    "type": "fixed",
                    "value": "#ffffff",
                    "field": "a",
                    "no_value": "#00ffff",
                },
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        [
                            "step",
                            ["get", "a"],
                            "#aa0000",
                            -4.292341999003442,
                            "#770000",
                            0.5740581144424383,
                            "#330000",
                            5.727211814984125,
                            "#000000",
                        ],
                        "#CC0000",
                    ],
                    "fill-opacity": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        0.4,
                        0.5,
                    ],
                    "fill-outline-color": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        "#ffffff",
                        "#00ffff",
                    ],
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#000000",
                            "boundaries": {
                                "lower": {"value": 5.727211814984125, "included": True},
                                "upper": {
                                    "value": 15.25702131719717,
                                    "included": True,
                                },
                            },
                        },
                        {
                            "color": "#330000",
                            "boundaries": {
                                "lower": {
                                    "value": 0.5740581144424383,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 5.727211814984125,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#770000",
                            "boundaries": {
                                "lower": {
                                    "value": -4.292341999003442,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 0.5740581144424383,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#aa0000",
                            "boundaries": {
                                "lower": {
                                    "value": -15.554792351427212,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -4.292341999003442,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#CC0000",
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_gauss_graduated_size_jenks(self):
        geo_layer = self.source.get_layer()

        random.seed(33)
        for _ in range(0, 1000):
            self._feature_factory(geo_layer, a=random.gauss(0, 5)),

        self.layer.main_style = {
            "map_style_type": "line",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "jenks",
                    "values": [3, 5, 10, 15],
                    "generate_legend": True,
                    "no_value": 7,
                },
                "line_color": {"type": "fixed", "value": "#ffffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "line",
                "paint": {
                    "line-width": [
                        "case",
                        ["==", ["typeof", ["get", "a"]], "number"],
                        [
                            "step",
                            ["get", "a"],
                            3,
                            -4.292341999003442,
                            5,
                            0.5740581144424383,
                            10,
                            5.727211814984125,
                            15,
                        ],
                        7,
                    ],
                    "line-color": "#ffffff",
                },
            },
        )
        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "line",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__line_width",
                    "items": [
                        {
                            "color": "#ffffff",
                            "strokeWidth": 15,
                            "boundaries": {
                                "lower": {"value": 5.727211814984125, "included": True},
                                "upper": {"value": 15.25702131719717, "included": True},
                            },
                        },
                        {
                            "color": "#ffffff",
                            "strokeWidth": 10,
                            "boundaries": {
                                "lower": {
                                    "value": 0.5740581144424383,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 5.727211814984125,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#ffffff",
                            "strokeWidth": 5,
                            "boundaries": {
                                "lower": {
                                    "value": -4.292341999003442,
                                    "included": True,
                                },
                                "upper": {
                                    "value": 0.5740581144424383,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#ffffff",
                            "strokeWidth": 3,
                            "boundaries": {
                                "lower": {
                                    "value": -15.554792351427212,
                                    "included": True,
                                },
                                "upper": {
                                    "value": -4.292341999003442,
                                    "included": False,
                                },
                            },
                        },
                        {
                            "color": "#ffffff",
                            "strokeWidth": 7,
                            "boundaries": {
                                "lower": {"value": None, "included": True},
                                "upper": {"value": None, "included": True},
                            },
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_categorize_colors_0value(self):

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "categorized",
                    "categories": [],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#00ffff"},
                "fill_nothing": {},  # Empty value
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {"type": "fill", "paint": {"fill-outline-color": "#00ffff"}},
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_categorize_colors(self):

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "categorized",
                    "categories": [
                        {"name": "Alaska", "value": "#fc34bc"},
                        {"name": "Cameroun", "value": "#2334bc"},
                        {"name": "France", "value": "#fc3445"},
                        {"name": "Canada", "value": "#fc15bc"},
                        {"name": "Groland", "value": "#1623bc"},
                    ],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#00ffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "match",
                        ["get", "a"],
                        "Alaska",
                        "#fc34bc",
                        "Cameroun",
                        "#2334bc",
                        "France",
                        "#fc3445",
                        "Canada",
                        "#fc15bc",
                        "Groland",
                        "#1623bc",
                        "#000000",
                    ],
                    "fill-outline-color": "#00ffff",
                },
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {"color": "#fc34bc", "label": "Alaska"},
                        {"color": "#2334bc", "label": "Cameroun"},
                        {"color": "#fc3445", "label": "France"},
                        {"color": "#fc15bc", "label": "Canada"},
                        {"color": "#1623bc", "label": "Groland"},
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_categorize_colors_with_no_value(self):

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "categorized",
                    "categories": [
                        {"name": "Alaska", "value": "#fc34bc"},
                        {"name": "Cameroun", "value": "#2334bc"},
                        {"name": "France", "value": "#fc3445"},
                        {"name": "Canada", "value": "#fc15bc"},
                        {"name": "Groland", "value": "#1623bc"},
                        {"name": "", "value": "#0023bc"},
                        {"name": None, "value": "#110000"},
                    ],
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#00ffff"},
            },
        }
        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "fill",
                "paint": {
                    "fill-color": [
                        "case",
                        ["has", "a"],
                        [
                            "match",
                            ["get", "a"],
                            "Alaska",
                            "#fc34bc",
                            "Cameroun",
                            "#2334bc",
                            "France",
                            "#fc3445",
                            "Canada",
                            "#fc15bc",
                            "Groland",
                            "#1623bc",
                            "",
                            "#0023bc",
                            "#110000",
                        ],
                        "#110000",
                    ],
                    "fill-outline-color": "#00ffff",
                },
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "square",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
                    "items": [
                        {
                            "color": "#fc34bc",
                            "label": "Alaska",
                        },
                        {"color": "#2334bc", "label": "Cameroun"},
                        {"color": "#fc3445", "label": "France"},
                        {"color": "#fc15bc", "label": "Canada"},
                        {"color": "#1623bc", "label": "Groland"},
                        {"color": "#0023bc", "label": ""},
                        {"color": "#110000", "label": None},
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_categorize_radius_with_no_value(self):

        self.layer.main_style = {
            "map_style_type": "circle",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "circle_radius": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "categorized",
                    "categories": [
                        {"name": "Alaska", "value": 10},
                        {"name": "Cameroun", "value": 20},
                        {"name": "France", "value": 30},
                        {"name": "Canada", "value": 40},
                        {"name": "Groland", "value": 50},
                        {"name": "", "value": 2},
                        {"name": None, "value": 0},
                    ],
                    "generate_legend": True,
                },
                "circle_color": {"type": "fixed", "value": "#00ffff"},
                "circle_stroke_color": {},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "circle",
                "paint": {
                    "circle-radius": [
                        "case",
                        ["has", "a"],
                        [
                            "match",
                            ["get", "a"],
                            "Alaska",
                            10,
                            "Cameroun",
                            20,
                            "France",
                            30,
                            "Canada",
                            40,
                            "Groland",
                            50,
                            "",
                            2,
                            0,
                        ],
                        0,
                    ],
                    "circle-color": "#00ffff",
                },
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "circle",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__circle_radius",
                    "items": [
                        {
                            "size": 10,
                            "label": "Alaska",
                            "color": "#00ffff",
                        },
                        {
                            "size": 20,
                            "label": "Cameroun",
                            "color": "#00ffff",
                        },
                        {
                            "size": 30,
                            "label": "France",
                            "color": "#00ffff",
                        },
                        {
                            "size": 40,
                            "label": "Canada",
                            "color": "#00ffff",
                        },
                        {
                            "size": 50,
                            "label": "Groland",
                            "color": "#00ffff",
                        },
                        {"size": 2, "label": "", "color": "#00ffff"},
                        {
                            "size": 0,
                            "label": None,
                            "color": "#00ffff",
                        },
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_categorize_values_with_no_value(self):

        self.layer.main_style = {
            "map_style_type": "line",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "line_width": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "categorized",
                    "categories": [
                        {"name": "Alaska", "value": 10},
                        {"name": "Cameroun", "value": 20},
                        {"name": "France", "value": 30},
                        {"name": "Canada", "value": 40},
                        {"name": "Groland", "value": 50},
                        {"name": "", "value": 2},
                        {"name": None, "value": 0},
                    ],
                    "generate_legend": True,
                },
                "line_color": {"type": "fixed", "value": "#00ffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "line",
                "paint": {
                    "line-width": [
                        "case",
                        ["has", "a"],
                        [
                            "match",
                            ["get", "a"],
                            "Alaska",
                            10,
                            "Cameroun",
                            20,
                            "France",
                            30,
                            "Canada",
                            40,
                            "Groland",
                            50,
                            "",
                            2,
                            0,
                        ],
                        0,
                    ],
                    "line-color": "#00ffff",
                },
            },
        )

        self.assertEqual(
            self.layer.legends,
            [
                {
                    "auto": True,
                    "shape": "line",
                    "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599__line_width",
                    "items": [
                        {
                            "strokeWidth": 10,
                            "label": "Alaska",
                            "color": "#00ffff",
                        },
                        {
                            "strokeWidth": 20,
                            "label": "Cameroun",
                            "color": "#00ffff",
                        },
                        {
                            "strokeWidth": 30,
                            "label": "France",
                            "color": "#00ffff",
                        },
                        {
                            "strokeWidth": 40,
                            "label": "Canada",
                            "color": "#00ffff",
                        },
                        {
                            "strokeWidth": 50,
                            "label": "Groland",
                            "color": "#00ffff",
                        },
                        {"strokeWidth": 2, "label": "", "color": "#00ffff"},
                        {"strokeWidth": 0, "label": None, "color": "#00ffff"},
                    ],
                    "title": "my_layer_name",
                }
            ],
        )

    def test_zoom_weight_style(self):

        self.layer.main_style = {
            "map_style_type": "icon",
            "type": "wizard",
            "min_zoom": 4,
            "max_zoom": 24,
            "weight": 50,
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "icon-image": {
                    "type": "fixed",
                    "value": "testicon",
                    "generate_legend": True,
                },
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "symbol",
                "minzoom": 4,
                "maxzoom": 24,
                "weight": 50,
                "layout": {"icon-image": "testicon"},
            },
        )

    def test_icon_style(self):

        self.layer.main_style = {
            "map_style_type": "icon",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "icon_image": {
                    "type": "fixed",
                    "value": "testicon",
                    "generate_legend": False,
                },
                "icon_color": {"type": "fixed", "value": "#00ffff"},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "symbol",
                "layout": {"icon-image": "testicon"},
                "paint": {"icon-color": "#00ffff"},
            },
        )

        self.assertEqual(
            self.layer.legends,
            [],
        )

    def test_text_style(self):

        self.layer.main_style = {
            "map_style_type": "text",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "text-size": {
                    "type": "fixed",
                    "value": 12,
                },
                "text-field": {
                    "type": "fixed",
                    "value": "{myfield}",
                },
                "text-allow-overlap": {
                    "type": "fixed",
                    "value": False,
                },
                "text_font": {"type": "fixed", "value": ["fontA", "fontB"]},
                "text_color": {"type": "fixed", "value": "#00ffbb"},
                "text_halo_color": {
                    "type": "fixed",
                    "value": "rgba(255, 255, 255, 0.8)",
                },
                "text_halo_width": {"type": "fixed", "value": 2},
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "symbol",
                "paint": {
                    "text-color": "#00ffbb",
                    "text-halo-color": "rgba(255, 255, 255, 0.8)",
                    "text-halo-width": 2,
                },
                "layout": {
                    "text-field": "{myfield}",
                    "text-allow-overlap": False,
                    "text-size": 12,
                    "text-font": ["fontA", "fontB"],
                },
            },
        )

        self.assertEqual(
            self.layer.legends,
            [],
        )

    def test_remove_unused_style(self):

        self.layer.main_style = {
            "map_style_type": "icon",
            "type": "wizard",
            "uid": "a48f4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "icon_image": {
                    "type": "fixed",
                    "value": "testicon",
                    "generate_legend": False,
                },
                "icon_color": {"type": "fixed", "value": "#00ffff"},
                "text-size": {
                    "type": "fixed",
                    "value": 12,
                },
                "text-field": {
                    "type": "fixed",
                    "value": "{myfield}",
                },
            },
        }

        self.layer.save()

        self.assertEqual(
            self.layer.main_style["map_style"],
            {
                "type": "symbol",
                "layout": {"icon-image": "testicon"},
                "paint": {"icon-color": "#00ffff"},
            },
        )

        self.assertEqual(
            self.layer.legends,
            [],
        )

    def test_clean_legend(self):
        geo_layer = self.source.get_layer()
        random.seed(33)
        for _ in range(0, 1000):
            self._feature_factory(geo_layer, a=random.gauss(0, 5)),

        self.layer.main_style = {
            "map_style_type": "fill",
            "type": "wizard",
            "uid": "bbbf4bd8-3715-4ea0-ae02-b1d827bcb599",
            "style": {
                "fill_color": {
                    "type": "variable",
                    "field": "a",
                    "analysis": "graduated",
                    "method": "jenks",
                    "values": ["#aa0000", "#770000", "#330000", "#000000"],
                    "no_value": "#000000",
                    "generate_legend": True,
                },
                "fill_outline_color": {"type": "fixed", "value": "#00ffff"},
            },
        }

        self.layer.save()

        self.assertEqual(len(self.layer.legends), 1)
        self.assertEqual(self.layer.legends[0]["auto"], True)
        self.assertEqual(
            self.layer.legends[0]["uid"],
            "bbbf4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
        )

        # Legend generation is off. Should keep the legend.
        self.layer.main_style["style"]["fill_color"]["generate_legend"] = False

        self.layer.save(preserve_legend=True)

        self.assertEqual(len(self.layer.legends), 1)
        self.assertEqual(self.layer.legends[0].get("auto", False), False)
        self.assertNotEqual(
            self.layer.legends[0].get("uid"),
            "bbbf4bd8-3715-4ea0-ae02-b1d827bcb599__fill_color",
        )

        # Add back the generated legend but previous one should be kept
        self.layer.main_style["style"]["fill_color"]["generate_legend"] = True

        self.layer.save(preserve_legend=True)

        self.assertEqual(len(self.layer.legends), 2)

        # Legend type is not variable anymore. Should drop the legend
        self.layer.main_style["style"]["fill_color"]["type"] = "none"

        self.layer.save(preserve_legend=True)

        self.assertEqual(len(self.layer.legends), 1)

        # Add back generated legend
        self.layer.main_style["style"]["fill_color"]["generate_legend"] = True
        self.layer.main_style["style"]["fill_color"]["type"] = "variable"

        self.layer.save(preserve_legend=True)

        self.assertEqual(len(self.layer.legends), 2)

        # Know we fully drop the style. Should drop the generated legend
        del self.layer.main_style["style"]["fill_color"]

        self.layer.save(preserve_legend=True)

        self.assertEqual(len(self.layer.legends), 1)
