import json
from io import StringIO
from unittest import mock

from django.test import TestCase
from geostore.models import Layer

from project.geosource.models import (
    CommandSource,
    CSVSource,
    Field,
    GeoJSONSource,
    GeometryTypes,
    PostGISSource,
    ShapefileSource,
    Source,
    WMTSSource,
)
from project.geosource.tests.helpers import get_file


class MockBackend(object):
    def __init__(self, *args, **kwargs):
        pass

    def get(self, id):
        return """{"result": {"%s": "NOT OK!"}}""" % id

    def get_key_for_task(self, id):
        return id


class MockAsyncResult(object):
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

        cls.geojson_source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )

    def test_source_str(self):
        self.assertEqual(str(self.source), "Toto - Source")

    def test_other_source_str(self):
        self.assertEqual(str(self.geojson_source), "Titi - GeoJSONSource")

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
        msg = "Can't find identifier field for this record"
        self.assertIn(msg, self.geojson_source.report.get("message", []))

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


class ModelGeoJSONSourceTestCase(TestCase):
    def test_get_file_as_dict(self):
        source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )

        self.assertEqual(
            source.get_file_as_dict(),
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"id": 1, "test": 5},
                        "geometry": {
                            "type": "Point",
                            "coordinates": [3.0808067321777344, 45.77488685869771],
                        },
                    }
                ],
            },
        )

    def test_get_file_as_dict_wrong_file(self):
        source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("bad.geojson"),
        )

        with self.assertRaises(json.decoder.JSONDecodeError):
            source.get_file_as_dict()

    def test_get_records_wrong_geom_file(self):
        source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("bad_geom.geojson"),
        )

        with self.assertRaises(ValueError) as m:
            source._get_records(1)
        self.assertEqual(
            "The record geometry seems invalid.",
            str(m.exception),
        )


class ModelShapeFileSourceTestCase(TestCase):
    def test_get_records(self):
        source = ShapefileSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            file=get_file("test.zip"),
        )

        records = source._get_records(1)
        self.assertEqual(records[0]["NOM"], "Trifouilli-les-Oies")
        self.assertEqual(records[0]["Insee"], 99999)
        self.assertEqual(records[0]["_geom_"].geom_typeid, GeometryTypes.Polygon)


class ModelCommandSourceTestCase(TestCase):
    def setUp(self):
        self.source = CommandSource.objects.create(
            name="Titi", geom_type=GeometryTypes.Point, command="command_test"
        )

    @mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_refresh_data(self, mocked_stdout, mock_index):
        mock_index.return_value = True
        with self.assertNumQueries(34):
            self.source.refresh_data()
        self.assertIn("Start refresh", mocked_stdout.getvalue())

    def test_get_records(self):
        self.assertEqual([], self.source._get_records())


class ModelWMTSSourceTestCase(TestCase):
    def setUp(self):
        self.source = WMTSSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point,
            tile_size=256,
            minzoom=14,
        )

    def test_get_records(self):
        self.assertEqual([], self.source._get_records())

    def test_get_status(self):
        self.assertEqual({"state": "DONT_NEED"}, self.source.get_status())

    def test_refresh_data(self):
        self.assertEqual({}, self.source.refresh_data())


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

        records = source._get_records()
        self.assertEqual(len(records), 6, len(records))
        with self.assertNumQueries(68):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len(records), row_count)

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

        records = source._get_records()
        self.assertEqual(len(records), 9, len(records))
        with self.assertNumQueries(92):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len(records), row_count)

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
        records = source._get_records()
        self.assertEqual(len(records), 9, len(records))
        with self.assertNumQueries(92):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len(records), row_count)

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
        records = source._get_records()
        # this entry as an empty column and should not be in records
        empty_entry = [
            record.get("photoEtablissement")
            for record in records
            if record.get("photoEtablissement")
        ]
        self.assertEqual(len(empty_entry), 0, empty_entry)
        with self.assertNumQueries(68):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len(records), row_count)

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
        records = source._get_records()
        self.assertEqual(len(records), 9, len(records))
        with self.assertNumQueries(92):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len(records), row_count)

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
        records = source._get_records()
        self.assertEqual(len(records), 10, len(records))
        with self.assertNumQueries(100):
            row_count = source.refresh_data()
        self.assertEqual(row_count["count"], len(records), row_count)

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
        with self.assertNumQueries(698):
            source.update_fields()
        fields = [f.name for f in Field.objects.filter(source=source)]
        self.assertTrue(fields == colnames)
