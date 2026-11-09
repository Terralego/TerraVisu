import io
import os
import tempfile
import zipfile
from io import BytesIO, StringIO
from unittest import mock

from celery.utils.log import LoggingProxy
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos.point import Point
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from django.test import TestCase
from geostore.models import Layer

from project.geosource.fields import LongURLField
from project.geosource.models import (
    CommandSource,
    CSVSource,
    Field,
    GeoFileSource,
    GeometryTypes,
    PostGISSource,
    Source,
    SourceReporting,
    WMTSSource,
    detect_boolean_fields,
    field_file_path,
    open_zipped_shapefile_layer,
    uploaded_file_path,
)
from project.geosource.tests.helpers import get_file


class MockBackend:
    def __init__(self, *args, **kwargs):
        pass

    def get(self, id):
        return f"""{{"result": {{"{id}": "NOT OK!"}}}}"""

    def get_key_for_task(self, id):
        return id


class MockAsyncResult:
    def __init__(self, task_id, *args, **kwargs):
        self.backend = MockBackend()

    @property
    def date_done(self):
        return "DONE"

    @property
    def state(self):
        return "ENDED"


class MockAsyncResultSuccess(MockAsyncResult):
    @property
    def result(self):
        return "OK!"

    def successful(self):
        return True

    def failed(self):
        return False


class MockAsyncResultFail(MockAsyncResult):
    @property
    def id(self):
        return 1

    @property
    def result(self):
        return {self.id: "NOT OK!"}

    def successful(self):
        return False

    def failed(self):
        return True


class ModelSourceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = Source.objects.create(
            name="Toto", geom_type=GeometryTypes.LineString
        )

        cls.geojson_source = GeoFileSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )

    def test_source_str(self):
        self.assertEqual(str(self.source), "Toto - (toto)")

    def test_other_source_str(self):
        self.assertEqual(str(self.geojson_source), "Titi - (titi)")

    def test_source_type(self):
        self.assertEqual(self.source.type, self.source.__class__)

    def test_query_filter(self):
        results = Source.objects.all()
        self.assertEqual(len(results), 2)

        results = Source.objects.filter(geom_type=GeometryTypes.LineString)
        self.assertEqual(len(results), 1)

    def test_geojsonsource_type(self):
        self.assertEqual(self.geojson_source.type, self.geojson_source.__class__)

    @mock.patch("elasticsearch.client.IndicesClient.create")
    @mock.patch("elasticsearch.client.IndicesClient.delete")
    def test_wrong_identifier_refresh(self, mocked_es_delete, mocked_es_create):
        self.geojson_source.id_field = "wrong_identifier"
        self.geojson_source.save()
        self.geojson_source.refresh_data()
        msg = "Line 0 - Can't find identifier 'wrong_identifier'"
        self.assertIn(msg, self.geojson_source.report.errors)

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    def test_delete(self, mock_index):
        mock_index.return_value = True
        self.geojson_source.refresh_data()
        self.assertEqual(Layer.objects.count(), 1)
        self.geojson_source.delete()
        self.assertEqual(Layer.objects.count(), 0)

    @mock.patch("project.geosource.models.AsyncResult", new=MockAsyncResultSuccess)
    def test_get_status(self):
        self.geojson_source.task_id = 1
        self.geojson_source.save()
        self.geojson_source.get_status()
        self.assertEqual(
            {"state": "ENDED", "result": "OK!", "done": "DONE"},
            self.geojson_source.get_status(),
        )

    @mock.patch("project.geosource.models.AsyncResult", new=MockAsyncResultFail)
    def test_get_status_fail(self):
        self.geojson_source.task_id = 1
        self.geojson_source.save()
        self.assertDictEqual(
            {"state": "ENDED", "done": "DONE", "result": {"error": "{1: 'NOT OK!'}"}},
            self.geojson_source.get_status(),
        )


class ModelFieldTestCase(TestCase):
    def test_field_str(self):
        source = Source.objects.create(name="Toto", geom_type=GeometryTypes.Point)
        field = Field.objects.create(source=source, name="tutu")
        self.assertEqual(str(field), "tutu (Toto - 5)")


class ModelPostGISSourceTestCase(TestCase):
    def setUp(self):
        self.geom_field = "geom"
        self.source = PostGISSource.objects.create(
            name="Toto", geom_type=GeometryTypes.Point, geom_field=self.geom_field
        )

    def test_source_geom_attribute(self):
        self.assertEqual(self.geom_field, self.source.SOURCE_GEOM_ATTRIBUTE)

    @mock.patch("psycopg2.connect", return_value=mock.Mock())
    def test_test_get_records(self, mock_con):
        self.source._get_records(1)
        mock_con.assert_called_once()


class ModelGeoFileSourceTestCase(TestCase):
    def test_get_records_wrong_file(self):
        source = GeoFileSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("bad.geojson"),
        )

        with self.assertRaises(GDALException):
            source._get_records()

    def test_get_records_wrong_geom_file(self):
        source = GeoFileSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("bad_geom.geojson"),
        )

        #        with self.assertRaises(ValueError) as m:
        records, errors, len_records = source._get_records(1)
        self.assertIn(
            'Feature fid 1: Invalid geometry pointer returned from "OGR_F_GetGeometryRef".',
            errors,
        )

    def test_get_records_shapefile(self):
        source = GeoFileSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("test.zip"),
        )

        records, errors, len_records = source._get_records(1)
        self.assertEqual(records[0]["NOM"], "Trifouilli-les-Oies")
        self.assertEqual(records[0]["Insee"], 99999)
        self.assertEqual(records[0]["_geom_"].geom_typeid, GeometryTypes.Polygon)

    def test_get_records_geopackage_default_layer(self):
        source = GeoFileSource.objects.create(
            name="gpkg_source",
            geom_type=GeometryTypes.Point,
            file=get_file("test.gpkg"),
        )
        records, errors, len_records = source._get_records()
        self.assertEqual(len(errors), 0)
        self.assertGreater(len_records, 0)
        self.assertIn("_geom_", records[0])
        self.assertEqual(records[0]["_geom_"].geom_typeid, GeometryTypes.Point)

    def test_get_records_geopackage_specific_layer(self):
        source = GeoFileSource.objects.create(
            name="gpkg_source_layer2",
            geom_type=GeometryTypes.Point,
            layer_name="layer_two",
            file=get_file("test.gpkg"),
        )
        records, errors, len_records = source._get_records()
        self.assertEqual(len(errors), 0)
        self.assertGreater(len_records, 0)

    def test_get_records_geopackage_invalid_layer_fallback(self):
        source = GeoFileSource.objects.create(
            name="gpkg_source_fallback",
            geom_type=GeometryTypes.Point,
            layer_name="non_existent_layer",
            file=get_file("test.gpkg"),
        )
        records, errors, len_records = source._get_records()
        self.assertEqual(len(errors), 0)
        self.assertGreater(len_records, 0)

    def test_get_records_zip_without_shp_returns_error(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            z.writestr("test.txt", "not a shp")
        zip_buffer.seek(0)
        source = GeoFileSource.objects.create(
            name="empty_zip_source",
            geom_type=GeometryTypes.Point,
            file=SimpleUploadedFile("empty.zip", zip_buffer.read()),
        )
        records, errors, len_records = source._get_records()
        self.assertEqual(records, [])
        self.assertEqual(errors, [{"error": "No .shp file found in archive"}])

    def test_get_records_limit(self):
        source = GeoFileSource.objects.create(
            name="limit_source",
            geom_type=GeometryTypes.Point,
            file=get_file("test.zip"),
        )
        records, errors, len_records = source._get_records(limit=1)
        self.assertEqual(len_records, 1)

    def test_records_from_layer_limit_break_multiple_features(self):
        source = GeoFileSource.objects.create(
            name="limit_gpkg_source",
            geom_type=GeometryTypes.Point,
        )
        feat1 = mock.MagicMock(
            geom=mock.MagicMock(geos=Point(0, 0, srid=4326)), fields=[]
        )
        feat2 = mock.MagicMock(
            geom=mock.MagicMock(geos=Point(1, 1, srid=4326)), fields=[]
        )
        mock_layer = mock.MagicMock(fields=[], field_types=[])
        mock_layer.__iter__.return_value = iter([feat1, feat2])
        records, errors, len_records = source._records_from_layer(
            mock_layer, 4326, limit=1
        )
        self.assertEqual(len(records), 1)

    def test_detect_boolean_fields_failure_returns_empty_set(self):
        result = detect_boolean_fields("/non/existent/path.gpkg", "layer")
        self.assertEqual(result, set())

    def test_uploaded_file_path_temporary_uploaded_file(self):
        temp_file = TemporaryUploadedFile(
            "temp.gpkg", "application/octet-stream", 0, "utf-8"
        )
        with uploaded_file_path(temp_file) as path:
            self.assertEqual(path, temp_file.temporary_file_path())

    def test_field_file_path_uncommitted(self):
        source = GeoFileSource(
            name="uncommitted",
            geom_type=GeometryTypes.Point,
            file=SimpleUploadedFile("test.geojson", b"{}"),
        )
        self.assertFalse(source.file._committed)
        with field_file_path(source.file) as path:
            self.assertTrue(os.path.exists(path))

    def test_open_zipped_shapefile_layer_no_shp_yields_none(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            z.writestr("readme.txt", "hello")
        zip_buffer.seek(0)
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.write(zip_buffer.read())
        tmp.close()
        try:
            with open_zipped_shapefile_layer(tmp.name) as layer:
                self.assertIsNone(layer)
        finally:
            os.unlink(tmp.name)

    def test_coerce_booleans(self):
        source = GeoFileSource.objects.create(
            name="bool_source",
            geom_type=GeometryTypes.Point,
        )
        self.assertEqual(source._coerce_booleans([], None), [])

        fake_type = mock.MagicMock()
        fake_type.__name__ = "OFTInteger"
        mock_layer = mock.MagicMock()
        mock_layer.fields = ["is_active"]
        mock_layer.field_types = [fake_type]

        records = [{"is_active": 1, "name": "a"}, {"is_active": 0, "name": "b"}]
        coerced = source._coerce_booleans(records, mock_layer)
        self.assertIs(coerced[0]["is_active"], True)
        self.assertIs(coerced[1]["is_active"], False)


class ModelCommandSourceTestCase(TestCase):
    def setUp(self):
        self.source = CommandSource.objects.create(
            name="Titi", geom_type=GeometryTypes.Point, command="command_test"
        )

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_refresh_data(self, mocked_stdout, mock_index):
        mock_index.return_value = True
        with self.assertNumQueries(36):
            self.source.refresh_data()
        self.assertIn("Start refresh", mocked_stdout.getvalue())

    @mock.patch("project.geosource.models.call_command")
    @mock.patch("project.geosource.models.refresh_data_done.send_robust")
    def test_refresh_data_with_logging_proxy(self, mock_signal, mock_call):
        self.source.clear_features = mock.MagicMock(return_value=(0, 0))
        self.source.get_layer = mock.MagicMock()
        fake_proxy = mock.MagicMock(spec=LoggingProxy)
        fake_stderr = mock.MagicMock()
        with (
            mock.patch("sys.stdout", fake_proxy),
            mock.patch("sys.stderr", fake_stderr),
        ):
            self.source._refresh_data()
            self.assertIsInstance(fake_proxy.buffer, BytesIO)
            self.assertIsNone(fake_proxy.encoding)
            self.assertIsInstance(fake_stderr.buffer, BytesIO)
            self.assertIsNone(fake_stderr.encoding)

    @mock.patch("project.geosource.models.call_command")
    @mock.patch("project.geosource.models.refresh_data_done.send_robust")
    def test_refresh_data_with_logging_proxy_attribute_error(
        self, mock_signal, mock_call
    ):
        self.source.clear_features = mock.MagicMock(return_value=(0, 0))
        self.source.get_layer = mock.MagicMock()
        fake_proxy = mock.MagicMock(spec=LoggingProxy)
        type(fake_proxy).buffer = mock.PropertyMock(side_effect=AttributeError)
        with mock.patch("sys.stdout", fake_proxy):
            self.source._refresh_data()

    def test_get_records(self):
        self.assertEqual([None, None, 0], self.source._get_records())


class ModelWMTSSourceTestCase(TestCase):
    def setUp(self):
        self.source = WMTSSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            tile_size=256,
            minzoom=14,
        )

    def test_get_records(self):
        self.assertEqual([None, None, 0], self.source._get_records())

    def test_get_status(self):
        self.assertEqual({"state": "DONT_NEED"}, self.source.get_status())

    def test_refresh_data(self):
        self.assertEqual({}, self.source.refresh_data())

    def test_refresh_status(self):
        self.assertIsNone(self.source.refresh_status)


class ModelCSVSourceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.base_settings = {
            "encoding": "UTF-8",
            "coordinate_reference_system": "EPSG_4326",
            "char_delimiter": "doublequote",
            "field_separator": "semicolon",
            "decimal_separator": "point",
            "use_header": True,
        }

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_get_records_with_two_columns_coordinates(
        self, mock_index_feature, mock_index
    ):
        mock_index.return_value = True
        source = CSVSource.objects.create(
            name="source",
            file=get_file("source.csv"),
            geom_type=GeometryTypes.Point,
            id_field="ID",
            settings={
                **self.base_settings,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )

        records, errors, len_records = source._get_records()
        self.assertEqual(len_records, 6, len_records)
        with self.assertNumQueries(78):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len_records, row_count)

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_get_records_with_one_column_coordinates(
        self, mock_index_feature, mock_index
    ):
        mock_index.return_value = True
        source = CSVSource.objects.create(
            name="source_xy",
            file=get_file("source_xy.csv"),
            geom_type=GeometryTypes.Point,
            id_field="ID",
            settings={
                **self.base_settings,
                "coordinates_field": "one_column",
                "latlong_field": "coordxy",
                "coordinates_separator": "comma",
                "coordinates_field_count": "xy",
            },
        )

        records, errors, len_records = source._get_records()
        self.assertEqual(len_records, 9, len_records)
        with self.assertNumQueries(105):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len_records, row_count)

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_get_records_with_decimal_separator_as_comma(
        self, mock_index_feature, mock_index
    ):
        mock_index.return_value = True
        source = CSVSource.objects.create(
            name="csv-source",
            file=get_file("source_xy_with_comma.csv"),
            geom_type=GeometryTypes.Point,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_4326",
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "comma",
                "use_header": True,
                "coordinates_field": "one_column",
                "latlong_field": "coordxy",
                "coordinates_separator": "point",
                "coordinates_field_count": "xy",
            },
        )
        records, errors, len_records = source._get_records()
        self.assertEqual(len_records, 9, len_records)
        with self.assertNumQueries(105):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len_records, row_count)

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_get_records_with_nulled_columns_ignored(
        self, mock_index_feature, mock_index
    ):
        mock_index.return_value = True
        source = CSVSource.objects.create(
            name="source",
            file=get_file("source.csv"),
            geom_type=GeometryTypes.Point,
            id_field="ID",
            settings={
                **self.base_settings,
                "ignore_columns": True,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        records, errors, len_records = source._get_records()
        # this entry as an empty column and should not be in records
        empty_entry = [
            record.get("photoEtablissement")
            for record in records
            if record.get("photoEtablissement")
        ]
        self.assertEqual(len(empty_entry), 0, empty_entry)
        with self.assertNumQueries(78):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len_records, row_count)

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_get_records_with_no_header_and_yx_csv(
        self, mock_index_feature, mock_index
    ):
        mock_index.return_value = True
        source = CSVSource.objects.create(
            name="source_xy_noheader",
            file=get_file("source_xy_noheader.csv"),
            geom_type=GeometryTypes.Point,
            id_field="1",
            settings={
                **self.base_settings,
                "use_header": False,
                "coordinates_field": "one_column",
                "latlong_field": "0",
                "coordinates_separator": "comma",
                "coordinates_field_count": "yx",
            },
        )
        records, errors, len_records = source._get_records()
        self.assertEqual(len_records, 9, len_records)
        with self.assertNumQueries(105):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len_records, row_count)

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_get_records_with_no_header_and_two_columns_csv(
        self, mock_index_feature, mock_index
    ):
        mock_index.return_value = True
        source = CSVSource.objects.create(
            name="source_noheader",
            file=get_file("source_noheader.csv"),
            geom_type=0,
            id_field="2",
            settings={
                **self.base_settings,
                "use_header": False,
                "coordinate_reference_system": "EPSG_2154",
                "coordinates_field": "two_columns",
                "latitude_field": "1",
                "longitude_field": "0",
            },
        )
        records, errors, len_records = source._get_records()
        self.assertEqual(len_records, 10, len_records)
        with self.assertNumQueries(114):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len_records, row_count)

    def test_update_fields_keep_order(self):
        source = CSVSource.objects.create(
            name="source",
            file=get_file("source.csv"),
            geom_type=GeometryTypes.Point,
            id_field="ID",
            settings={
                **self.base_settings,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        sheet = source.get_file_as_sheet()
        sheet.name_columns_by_row(0)
        colnames = [name for name in sheet.colnames if name not in ("XCOORD", "YCOORD")]
        with self.assertNumQueries(699):
            source.update_fields()
        fields = [f.name for f in Field.objects.filter(source=source)]
        self.assertTrue(fields == colnames)

    def tesst_get_file_as_sheet_create_report_if_none_exists(self):
        source = CSVSource.objects.create(
            name="source-csv",
            file=get_file("source.csv"),
            geom_type=GeometryTypes.Point,
            id_field="ID",
            settings={
                **self.base_settings,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        self.assertIsNone(source.report)
        source.get_file_as_sheet()
        self.assertIsInstance(self.report, SourceReporting)
        self.assertIsNotNone(self.report.id)


class SourceReportingTestCase(TestCase):
    def setUp(self):
        self.source = GeoFileSource.objects.create(
            name="test-geojson",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )

    def tearDown(self):
        self.source.delete()

    @mock.patch("elasticsearch.client.IndicesClient.create")
    @mock.patch("elasticsearch.client.IndicesClient.delete")
    def test_source_refresh_data_create_reporting(self, mock_es_create, mock_es_delete):
        self.source.refresh_data()
        self.assertIsNotNone(self.source.report)

    @mock.patch("elasticsearch.client.IndicesClient.create")
    @mock.patch("elasticsearch.client.IndicesClient.delete")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_added_lines_are_reported(
        self, mock_es_create, mock_es_delete, mock_es_index, mock_es_index_feature
    ):
        self.source.refresh_data()
        self.assertEqual(self.source.report.added_lines, 1)

    @mock.patch("elasticsearch.client.IndicesClient.create")
    @mock.patch("elasticsearch.client.IndicesClient.delete")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_deleted_lines_are_reported(
        self, mock_es_create, mock_es_delete, mock_es_index, mock_es_index_feature
    ):
        self.source.refresh_data()
        self.source.file = get_file("bad_geom.geojson")
        self.source.save()
        self.source.refresh_data()
        self.assertEqual(self.source.report.deleted_lines, 1)

    @mock.patch("elasticsearch.client.IndicesClient.create")
    @mock.patch("elasticsearch.client.IndicesClient.delete")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_modified_lines_are_reported(
        self, mock_es_create, mock_es_delete, mock_es_index, mock_es_index_feature
    ):
        self.source.refresh_data()
        self.source.file = get_file("test_2.geojson")
        self.source.save()
        self.source.refresh_data()
        self.assertEqual(self.source.report.modified_lines, 1)

    def test_reset_method(self):
        report = SourceReporting.objects.create(
            status=SourceReporting.Status.SUCCESS.value,
            message="Some report message",
            added_lines=42,
            modified_lines=42,
            deleted_lines=42,
            errors=["error 1", "error 2", "error 3"],
        )
        report.reset()
        self.assertEqual(report.message, "")
        self.assertEqual(report.added_lines, 0)
        self.assertEqual(report.modified_lines, 0)
        self.assertEqual(report.deleted_lines, 0)
        self.assertEqual(report.errors, [])

    @mock.patch("elasticsearch.client.IndicesClient.create")
    @mock.patch("elasticsearch.client.IndicesClient.delete")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_partial_refresh_trigger_warning(
        self, mock_es_create, mock_es_delete, mock_es_index, mock_es_index_feature
    ):
        """Calling refresh_data on a source with some row containing error should lead
        to have less row being refresh than the total row count (partial refresh).
        The report Status shoule be WARNING"""

        # Mocking _get_records to return some incorret row
        mocked_rows = (
            [
                {"_geom_": Point(2, 42, srid=4326), "id": 1, "test": 5},
                {"_geom_": "wrong geom"},
            ],
            [],
            2,
        )
        self.source._get_records = mock.MagicMock(return_value=mocked_rows)
        self.source.refresh_data()
        self.source.refresh_from_db()
        self.assertEqual(
            self.source.report.status,
            SourceReporting.Status.WARNING.value,
            self.source.report.get_status_display(),
        )

    def test_report_str(self):
        report = SourceReporting.objects.create(
            status=SourceReporting.Status.SUCCESS.value
        )
        self.assertEqual(str(report), str(SourceReporting.Status.SUCCESS.value))

    @mock.patch("elasticsearch.client.IndicesClient.create")
    @mock.patch("elasticsearch.client.IndicesClient.delete")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
    def test_update_feature_exception_records_error_and_rolls_back(
        self, mock_es_create, mock_es_delete, mock_es_index, mock_es_index_feature
    ):
        mocked_rows = (
            [
                {"_geom_": Point(2, 42, srid=4326), "id": 1, "test": 5},
            ],
            [],
            1,
        )
        self.source._get_records = mock.MagicMock(return_value=mocked_rows)
        with mock.patch.object(
            self.source,
            "update_feature",
            side_effect=Exception("Update feature failed"),
        ):
            self.source.refresh_data()
        self.source.refresh_from_db()
        self.assertTrue(
            any("Update feature failed" in err for err in self.source.report.errors)
        )


class LongURLFieldTestCase(TestCase):
    def test_formfield(self):
        field = LongURLField()
        form_field = field.formfield()
        from django import forms

        self.assertIsInstance(form_field, forms.URLField)
