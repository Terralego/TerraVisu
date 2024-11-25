from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from geostore.models import Layer
from rest_framework.exceptions import MethodNotAllowed

from project.geosource.models import GeoJSONSource, GeometryTypes
from project.geosource.tests.helpers import get_file


def side_effect(method, list, **kwargs):
    return "Task"


class ResyncAllSourcesTestCase(TestCase):
    def setUp(self):
        self.source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )

    def test_resync_all_sources(self):
        out = StringIO()
        with mock.patch(
            "project.geosource.models.GeoJSONSource.refresh_data"
        ) as mocked, mock.patch(
            "project.geosource.mixins.CeleryCallMethodsMixin.update_status",
            return_value=False,
        ):
            call_command("resync_all_sources", stdout=out)

        mocked.assert_called_once()

    def test_resync_all_sources_sync(self):
        out = StringIO()
        with mock.patch(
            "project.geosource.models.GeoJSONSource.refresh_data"
        ) as mocked:
            call_command("resync_all_sources", sync=True, stdout=out)

        mocked.assert_called_once()

    def test_resync_source(self):
        out = StringIO()

        def side_effect(method, list, **kwargs):
            return "Task"

        with mock.patch(
            "project.geosource.models.GeoJSONSource.refresh_data"
        ) as mocked, mock.patch(
            "project.geosource.mixins.CeleryCallMethodsMixin.update_status",
            return_value=False,
        ):
            call_command("resync_source", pk=self.source.id, stdout=out)
        mocked.assert_called_once()

    def test_resync_source_sync(self):
        out = StringIO()
        with mock.patch(
            "project.geosource.models.GeoJSONSource.refresh_data"
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
        with mock.patch(
            "project.geosource.models.GeoJSONSource.refresh_data"
        ) as mocked, mock.patch(
            "project.geosource.mixins.CeleryCallMethodsMixin.update_status",
            return_value=False,
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
