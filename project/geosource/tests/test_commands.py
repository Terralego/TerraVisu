from io import StringIO
from unittest import mock

from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.test import TestCase
from geostore.models import Feature, Layer
from rest_framework.exceptions import MethodNotAllowed

from project.geosource.elasticsearch.index import LayerESIndex
from project.geosource.management.commands.helpers import (
    BaseCommandSource,
    DSCommandSource,
)
from project.geosource.models import Field, FieldTypes, GeoFileSource, GeometryTypes
from project.geosource.tests.helpers import get_file


def side_effect(method, list, **kwargs):
    return "Task"


class ResyncAllSourcesTestCase(TestCase):
    def setUp(self):
        self.source = GeoFileSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )

    def test_resync_all_sources(self):
        out = StringIO()
        with (
            mock.patch("project.geosource.models.GeoFileSource.refresh_data") as mocked,
            mock.patch(
                "project.geosource.mixins.CeleryCallMethodsMixin.update_status",
                return_value=False,
            ),
        ):
            call_command("resync_all_sources", stdout=out)

        mocked.assert_called_once()

    def test_resync_all_sources_sync(self):
        out = StringIO()
        with mock.patch(
            "project.geosource.models.GeoFileSource.refresh_data"
        ) as mocked:
            call_command("resync_all_sources", sync=True, stdout=out)

        mocked.assert_called_once()

    def test_resync_source(self):
        out = StringIO()

        def side_effect(method, list, **kwargs):
            return "Task"

        with (
            mock.patch("project.geosource.models.GeoFileSource.refresh_data") as mocked,
            mock.patch(
                "project.geosource.mixins.CeleryCallMethodsMixin.update_status",
                return_value=False,
            ),
        ):
            call_command("resync_source", pk=self.source.id, stdout=out)
        mocked.assert_called_once()

    def test_resync_source_sync(self):
        out = StringIO()
        with mock.patch(
            "project.geosource.models.GeoFileSource.refresh_data"
        ) as mocked:
            call_command("resync_source", pk=self.source.id, sync=True, stdout=out)

        mocked.assert_called_once()

    def test_resync_all_sources_fail(self):
        out = StringIO()
        with mock.patch(
            "project.geosource.mixins.CeleryCallMethodsMixin.update_status"
        ):
            with mock.patch(
                "project.geosource.mixins.CeleryCallMethodsMixin.can_sync",
                new_callable=mock.PropertyMock,
                return_value=False,
            ):
                with self.assertRaisesRegex(
                    MethodNotAllowed,
                    'Method "One job is still running on this source" not allowed.',
                ):
                    call_command("resync_all_sources", stdout=out)

    def test_resync_all_sources_fail_force(self):
        out = StringIO()
        with (
            mock.patch("project.geosource.models.GeoFileSource.refresh_data") as mocked,
            mock.patch(
                "project.geosource.mixins.CeleryCallMethodsMixin.update_status",
                return_value=False,
            ),
        ):
            with mock.patch(
                "project.geosource.mixins.CeleryCallMethodsMixin.can_sync",
                new_callable=mock.PropertyMock,
                return_value=False,
            ):
                call_command("resync_all_sources", force=True, stdout=out)
        mocked.assert_called_once()


class IndexToESTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.layer_1 = Layer.objects.create(name="layer_1")
        Layer.objects.create(name="layer_2")

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    def test_index_single_layer(self, mock_index):
        mock_index.return_value = True
        out = StringIO()
        call_command("index_to_es", layer=self.layer_1.pk, stdout=out)
        self.assertIn("Indexing layer layer_1", out.getvalue())

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    def test_index_all_layers(self, mock_index):
        mock_index.return_value = True
        out = StringIO()
        call_command("index_to_es", stdout=out)
        self.assertIn("Indexing all layers", out.getvalue())

    def test_resync_all_sources_with_ask_confirmation(self):
        GeoFileSource.objects.create(
            name="ask_source",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        out = StringIO()
        with (
            mock.patch("builtins.input", return_value="y"),
            mock.patch("project.geosource.models.GeoFileSource.refresh_data") as mocked,
        ):
            call_command("resync_all_sources", ask=True, sync=True, stdout=out)
        mocked.assert_called_once()

    @mock.patch(
        "project.geosource.management.commands.auto_refresh_sources.auto_refresh_source"
    )
    def test_auto_refresh_sources_command(self, mock_auto_refresh):
        call_command("auto_refresh_sources")
        mock_auto_refresh.assert_called_once()


class CommandHelpersAbstractMethodsTestCase(TestCase):
    def test_base_command_source_not_implemented_methods(self):
        cmd = BaseCommandSource()
        with self.assertRaises(NotImplementedError):
            cmd.get_data()
        with self.assertRaises(NotImplementedError):
            cmd.parse_data_to_feature({})
        with self.assertRaises(NotImplementedError):
            cmd.update_source_fields({})

    def test_ds_command_source_without_path_raises_not_implemented(self):
        cmd = DSCommandSource()
        with self.assertRaises(NotImplementedError):
            cmd.get_data_source()


class LayerESIndexTestCase(TestCase):
    def test_create_index_without_matching_source_returns_early(self):
        layer = Layer.objects.create(name="orphan_layer")
        mock_client = mock.MagicMock()
        es_index = LayerESIndex(layer, client=mock_client)
        es_index.create_index()
        mock_client.indices.create.assert_not_called()

    def test_create_index_and_format_boolean_records(self):
        source = GeoFileSource.objects.create(
            name="es_test_source",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        Field.objects.create(
            source=source, name="title", data_type=FieldTypes.String.value
        )
        Field.objects.create(
            source=source, name="count", data_type=FieldTypes.Integer.value
        )
        Field.objects.create(
            source=source, name="flag_true", data_type=FieldTypes.Boolean.value
        )
        Field.objects.create(
            source=source, name="flag_false", data_type=FieldTypes.Boolean.value
        )
        Field.objects.create(
            source=source, name="flag_other_str", data_type=FieldTypes.Boolean.value
        )
        Field.objects.create(
            source=source, name="flag_int", data_type=FieldTypes.Boolean.value
        )
        Field.objects.create(
            source=source, name="flag_bool", data_type=FieldTypes.Boolean.value
        )
        Field.objects.create(
            source=source, name="flag_none", data_type=FieldTypes.Boolean.value
        )
        Field.objects.create(
            source=source, name="ignored", data_type=FieldTypes.Undefined.value
        )
        layer = source.get_layer()
        mock_client = mock.MagicMock()
        es_index = LayerESIndex(layer, client=mock_client)
        es_index.create_index()
        mock_client.indices.create.assert_called_once()

        feature = Feature.objects.create(
            layer=layer,
            identifier="1",
            geom=Point(0, 0, srid=4326),
            properties={
                "title": "hello",
                "count": 10,
                "flag_true": "true",
                "flag_false": "0",
                "flag_other_str": "maybe",
                "flag_int": 1,
                "flag_bool": True,
                "flag_none": None,
            },
        )
        record = es_index._get_formatted_record(layer.name, feature)
        doc = record["document"]
        self.assertIs(doc["flag_true"], True)
        self.assertIs(doc["flag_false"], False)
        self.assertEqual(doc["flag_other_str"], "maybe")
        self.assertIs(doc["flag_int"], True)
        self.assertIs(doc["flag_bool"], True)
        self.assertEqual(doc["title"], "hello")
