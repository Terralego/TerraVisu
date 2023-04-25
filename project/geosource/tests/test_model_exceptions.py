import json
from unittest.mock import PropertyMock, patch

import pyexcel
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from psycopg2 import OperationalError

from project.geosource.models import (
    CSVSource,
    GeoJSONSource,
    GeometryTypes,
    PostGISSource,
    ShapefileSource,
)
from project.geosource.tests.helpers import get_file


def mocked_decode():
    raise UnicodeDecodeError("Wrong")


class MockedBytes(PropertyMock):
    def decode(self):
        raise UnicodeDecodeError("wrong")


@patch("elasticsearch.client.IndicesClient.create")
@patch("elasticsearch.client.IndicesClient.delete")
class CSVSourceExceptionsTestCase(TestCase):
    def test_csv_with_wrong_x_coord(self, mocked_es_delete, mocked_es_create):
        source = CSVSource.objects.create(
            file=get_file("source.csv"),
            geom_type=0,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_4326",
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "two_columns",
                "longitude_field": "X",  # wrong on purpose
                "latitude_field": "YCOORDS",
            },
        )
        msg = "X is not a valid coordinate field"
        with self.assertRaisesMessage(ValueError, msg):
            source._get_records()
            self.assertIn(msg, source.report.get("message", []))

    def test_csv_with_wrong_y_coord(self, mocked_es_delete, mocked_es_create):
        source = CSVSource.objects.create(
            file=get_file("source.csv"),
            geom_type=0,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_4326",
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "Y",  # Wrong on purpose
            },
        )
        msg = "Y is not a valid coordinate field"
        with self.assertRaisesMessage(ValueError, msg):
            source._get_records()
            self.assertIn(msg, source.report.get("message", []))

    def test_invalid_csv_file_raise_value_error(
        self, mocked_es_delete, mocked_es_create
    ):
        source = CSVSource.objects.create(
            file=SimpleUploadedFile("not_a_csv", b"some content"),
            geom_type=0,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_4326",
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        # assert pyexcel exception
        msg = "Provided CSV file is invalid"
        with self.assertRaisesMessage(
            (pyexcel.exceptions.FileTypeNotSupported, Exception), msg
        ):
            source._get_records()
            self.assertIn(msg, source.report.get("message", []))

    def test_invalid_coordinate_format_raise_error(
        self, mocked_es_delete, mocked_es_create
    ):
        source = CSVSource.objects.create(
            file=get_file("source.csv"),
            geom_type=0,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_4326",
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "one_column",
                "latlong_field": "coordxy",
                "coordinates_separator": "comma",
                "coordinates_field_count": "xy",
            },
        )
        source._get_records()
        self.assertIn(
            "coordxy is not a valid coordinate field", source.report["message"]
        )

    def test_coordinates_system_without_digit_srid_raise_value_error(
        self, mocked_es_delete, mocked_es_create
    ):
        source = CSVSource.objects.create(
            file=get_file("source.csv"),
            geom_type=0,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_SRID",  # Wrong on purpose
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        with self.assertRaises(ValueError):
            source._get_records()

    def test_coordinates_systems_malformed_raise_index_error(
        self, mocked_es_delete, mocked_es_create
    ):
        source = CSVSource.objects.create(
            file=get_file("source.csv"),
            geom_type=0,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "4326",  # Wrong on purpose
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        with self.assertRaises(IndexError):
            source._get_records()

    def test_source_empty_csv(self, mocked_es_delete, mocked_es_create):
        source = CSVSource.objects.create(
            file=get_file("source_empty.csv"),
            geom_type=0,
            id_field="ID",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_4326",  # Wrong on purpose
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        with self.assertRaisesRegex(Exception, "Failed to refresh data"):
            source.refresh_data()

    def test_invalid_id_field_report_message_when_refreshing_data(
        self, mocked_es_delete, mocked_es_create
    ):
        source = CSVSource.objects.create(
            name="csv-source",
            file=get_file("source.csv"),
            geom_type=0,
            id_field="identifier",
            settings={
                "encoding": "UTF-8",
                "coordinate_reference_system": "EPSG_4326",  # Wrong on purpose
                "char_delimiter": "doublequote",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "use_header": True,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        msg = "Can't find identifier field for this record"
        source.refresh_data()
        self.assertIn(msg, source.report.get("message", []))


@patch("elasticsearch.client.IndicesClient.create")
@patch("elasticsearch.client.IndicesClient.delete")
class GeoJSONSourceExceptionsTestCase(TestCase):
    def test_source_geojson_with_wrong_id_report_message(
        self, mocked_es_delete, mocked_es_create
    ):
        geodict = {
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
        }
        geojson = json.dumps(geodict)
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=SimpleUploadedFile("geojson", bytes(geojson, encoding="UTF-8")),
            id_field="gid",  # wrong id field
        )
        msg = "Can't find identifier field for this record"
        source.refresh_data()
        self.assertIn(msg, source.report.get("message", []))


@patch("elasticsearch.client.IndicesClient.create")
@patch("elasticsearch.client.IndicesClient.delete")
class PostGISSourceExceptionsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = PostGISSource.objects.create(
            name="source_test",
            geom_type=GeometryTypes.Point,
            geom_field="geom",
        )

    @patch("psycopg2.connect", side_effect=OperationalError("Connection error"))
    def test_operationalerror_on_db_connect_is_reported(
        self, mocked_es_delete, mocked_es_create, mocked_connect
    ):
        with self.assertRaises(OperationalError):
            self.source._db_connection()
            mocked_connect.assert_called_once()
            self.assertIn("Connection error", self.source.report.get("message", []))


@patch("elasticsearch.client.IndicesClient.create")
@patch("elasticsearch.client.IndicesClient.delete")
class ShapefileSourceExceptionsTestCase(TestCase):
    def test_wrong_id_report_message_on_refresh_and_get_reported(
        self, mocked_es_delete, mocked_es_create
    ):
        source = ShapefileSource.objects.create(
            name="test_shapefile",
            geom_type=GeometryTypes.Point,
            file=get_file("test.zip"),
            id_field="wrongid",
        )
        msg = "Can't find identifier field for this record"
        source.refresh_data()
        self.assertIn(msg, source.report.get("message", []))
