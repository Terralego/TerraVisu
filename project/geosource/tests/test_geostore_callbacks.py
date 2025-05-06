from unittest import mock

from django.contrib.auth.models import Group
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from geostore.models import Feature, Layer

from project.geosource import geostore_callbacks
from project.geosource.models import GeoJSONSource, GeometryTypes
from project.geosource.tests.helpers import get_file


class GeostoreCallBacksTestCase(TestCase):
    def test_layer_callback(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        source.groups.add(group)
        layer = geostore_callbacks.layer_callback(source)
        self.assertEqual(layer.authorized_groups.first().name, "Group")

    def test_feature_callback(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        source.groups.add(group)
        layer = Layer.objects.create(name="test")
        feature, _ = geostore_callbacks.feature_callback(
            source, layer, "id", GEOSGeometry("POINT (0 0)", srid=3857), {}
        )
        self.assertEqual(feature.geom.srid, 4326)

    def test_feature_callback_fail(self):
        with self.assertLogs("project.geosource.geostore_callbacks", "WARNING") as log:
            group = Group.objects.create(name="Group")
            source = GeoJSONSource.objects.create(
                name="test",
                geom_type=GeometryTypes.Point,
                file=get_file("test.geojson"),
            )
            source.groups.add(group)
            layer = Layer.objects.create(name="test")

            geostore_callbacks.feature_callback(
                source, layer, "id", "Not a Point", {"property": "Hola"}
            )
            self.assertTrue(
                log.output[0].endswith(
                    "One record was ignored from source, because of invalid geometry: {'property': 'Hola'}"
                )
            )

    def test_clean_features(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        source.groups.add(group)
        layer = Layer.objects.create(name="test")
        Feature.objects.create(layer=layer, geom=GEOSGeometry("POINT (0 0)"))
        geostore_callbacks.clear_features(source, layer, layer.updated_at)

    def test_delete_layer(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        source.groups.add(group)
        layer = Layer.objects.create(name="test")
        Feature.objects.create(layer=layer, geom=GEOSGeometry("POINT (0 0)"))
        geostore_callbacks.delete_layer(source)

    @mock.patch(
        "project.geosource.geostore_callbacks.GEOSGeometry", side_effect=ValueError()
    )
    def test_feature_callback_return_none_tuple_when_valueerror(self, mocked_geos):
        # Setup test data
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        source.groups.add(group)
        layer = Layer.objects.create(name="test")

        # Testing
        feature, created = geostore_callbacks.feature_callback(
            source, layer, "id", "Not a Point", {"property": "Hola"}
        )
        self.assertIsNone(feature)
        self.assertIsNone(created)
