import json
from unittest.mock import Mock, PropertyMock, patch

import pyexcel
from django.contrib.gis.gdal.error import GDALException
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from psycopg2 import OperationalError

from project.geosource.exceptions import CSVSourceException, SourceException
from project.geosource.models import (
    CSVSource,
    GeoJSONSource,
    GeometryTypes,
    PostGISSource,
    ShapefileSource,
    Source,
    SourceReporting,
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
        _, errors = source._get_records()
        self.assertIn("Sheet row 0 - X is not a valid coordinate field", errors)

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
        _, errors = source._get_records()
        self.assertIn("Sheet row 0 - Y is not a valid coordinate field", errors)

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
        self.assertIsNone(source.report)
        with self.assertRaisesMessage(
            (pyexcel.exceptions.FileTypeNotSupported, Exception), msg
        ):
            source._get_records()
            self.assertIsInstance(source.report, SourceReporting)
            self.assertIn(msg, source.report.get("message", []))

    def test_invalid_coordinate_format_error_handle(
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
        _, errors = source._get_records()
        self.assertIn("Sheet row 0 - coordxy is not a valid coordinate field", errors)

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
        with self.assertRaisesMessage(CSVSourceException, "Invalid SRID: EPSG_SRID"):
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
        with self.assertRaisesMessage(CSVSourceException, "Invalid SRID: 4326"):
            source._get_records()

    # TODO: Move to test_models.py instead, since no exception is raised anymore
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
        # with self.assertRaisesRegex(Exception, "Failed to refresh data"):
        source.refresh_data()
        self.assertIn("Failed to refresh data", source.report.message)

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
        msg = "Line 0 - Can't find identifier 'identifier'"
        source.refresh_data()
        self.assertIn(msg, source.report.errors)

    @patch("project.geosource.models.GEOSGeometry", side_effect=GDALException())
    def test_gdal_exception_set_report_to_warning(
        self, mocked_es_create, mocked_es_delete, mock_geos
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
        _, errors = source._get_records()
        msg = "Sheet row 0 - One of source's record has invalid geometry: Point(930077.50743 6922202.67316) srid=4326"
        self.assertIn(msg, errors)

    @patch("project.geosource.models.pyexcel.get_sheet", side_effect=Exception())
    def test_get_file_as_sheet_exception_create_new_report_if_none(
        self, mocked_es_create, mocked_es_delete, mocked_pyexcel
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
        self.assertIsNone(source.report)
        with self.assertRaises(Exception):
            source.get_file_as_sheet()
            self.assertIsInstance(source.report, SourceReporting)

    def test_valueerror_raised_in_extract_coordinate_create_report_if_none(
        self, mocked_es_create, mocked_es_delete
    ):
        source = CSVSource.objects.create(
            name="csv-source",
            file=get_file("source.csv"),
            geom_type=0,
            id_field="identifier",
        )
        self.assertIsNone(source.report)
        with self.assertRaises(CSVSourceException):
            # put some nonsens data to trigger ValueError raise
            source._extract_coordinates(
                ["a", "b", "c"], [1, 2, 3], ["foo", "bar", "foobar"]
            )
            self.assertIsInstance(source.report, SourceReporting)


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
        msg = "Line 0 - Can't find identifier 'gid'"
        source.refresh_data()
        self.assertIn(msg, source.report.errors)


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
            self.assertIn("Connection error", self.source.report.message)


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
        msg = "Line 0 - Can't find identifier 'wrongid'"
        source.refresh_data()
        self.assertIn(msg, source.report.errors)


@patch("elasticsearch.client.IndicesClient.create")
@patch("elasticsearch.client.IndicesClient.delete")
class SourceExceptionTestCase(TestCase):
    def test_source_exception_raised_create_a_report(self, mocked_es_delete, mocked_es_create):
        def side_effect(*args, **kwargs):
            raise SourceException("Error")

        source = Source.objects.create(name="mocked-source")
        source._refresh_data = Mock(side_effect=side_effect)
        self.assertIsNone(source.report)

        # Since we mocked "_refresh_data", we need to init an empty SourceReporting manually
        source.report = SourceReporting.objects.create()
        source.refresh_data()
        self.assertIsInstance(source.report, SourceReporting)
        self.assertEqual(source.report.status, SourceReporting.Status.ERROR.value)
        self.assertEqual(
            source.report.message, "Error"
        )  # Should be the message of the exception raised
