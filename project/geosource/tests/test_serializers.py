from unittest.mock import MagicMock, patch

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from project.geosource.models import (
    CSVSource,
    Field,
    GeoFileSource,
    Source,
    SourceReporting,
)
from project.geosource.serializers import (
    CommandSourceSerializer,
    CSVSourceSerializer,
    GeoFileSourceSerializer,
    PostGISSourceSerializer,
    SourceSerializer,
    WMTSSourceSerialize,
)
from project.geosource.tests.helpers import get_file


class CSVSourceSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings_data = {
            "encoding": "UTF-8",
            "coordinate_reference_system": "EPSG_4326",
            "field_separator": "semicolon",
            "decimal_separator": "point",
            "char_delimiter": "doublequote",
            "number_lines_to_ignore": 0,
            "use_header": True,
            "ignore_columns": False,
        }
        cls.csv = get_file("source.csv")

    # mock validation method, the file validity does not matter for this test
    @patch.object(CSVSourceSerializer, "_validate_field_infos")
    def test_to_internal_value_put_data_into_settings(self, mocked_method):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        settings = {
            **self.settings_data,
            "coordinates_field": "two_columns",
            "latitude_field": "lat",
            "longitude_field": "long",
        }
        data = {
            "file": [csv],
            "_type": "CSVSource",
            "name": "test",
            **settings,
        }
        serializer = CSVSourceSerializer(data=data)
        serializer.is_valid()
        serializer.save()

        self.assertTrue(
            CSVSource.objects.filter(settings=settings).exists(), serializer.errors
        )

    # mock validation method, the file validity does not matter for this test
    @patch.object(CSVSourceSerializer, "_validate_field_infos")
    def test_to_internal_value_put_one_columns_data_into_settings(self, mocked_method):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        settings = {
            **self.settings_data,
            "coordinates_field": "one_column",
            "coordinates_separator": "comma",
            "latlong_field": "COORDXY",
            "coordinates_field_count": "xy",
        }
        data = {
            "file": [csv],
            "_type": "CSVSource",
            "name": "test",
            **settings,
        }
        serializer = CSVSourceSerializer(data=data)
        serializer.is_valid()
        serializer.save()

        self.assertTrue(CSVSource.objects.filter(settings=settings).exists())

    def test_data_representation_is_correct(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        data = {
            "file": csv,
            "geom_type": 0,
            "name": "test",
            "settings": {
                **self.settings_data,
                "coordinates_field": "two_columns",
                "latitude_field": "lat",
                "longitude_field": "long",
            },
        }
        csv_source = CSVSource.objects.create(**data)
        serializer = CSVSourceSerializer(csv_source)

        # assert at least one of the settings element is at root level in serializer data
        # if it works for one, it works for all the other
        self.assertEqual(
            serializer.data.get("coordinate_reference_system"),
            csv_source.settings["coordinate_reference_system"],
        )

    def test_data_representation_is_correct_with_one_column_coordinates(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        data = {
            "file": csv,
            "geom_type": 0,
            "name": "test",
            "settings": {
                **self.settings_data,
                "coordinates_field": "one_columns",
                "coordinates_separator": "comma",
                "latlong_field": "COORDXY",
                "coordinates_field_count": "xy",
            },
        }
        csv_source = CSVSource.objects.create(**data)
        serializer = CSVSourceSerializer(csv_source)

        # assert at least one of the settings element is at root level in serializer data
        # if it works for one, it works for all the other
        self.assertEqual(
            serializer.data.get("coordinate_reference_system"),
            csv_source.settings["coordinate_reference_system"],
        )

    def test_missing_lat_and_long_field_raise_errors(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        data = {
            "file": [csv],
            "_type": "CSVSource",
            "name": "test",
            "encoding": "UTF-8",
            "coordinate_reference_system": "EPSG_4326",
            "coordinates_field": "two_columns",
            "field_separator": "semicolon",
            "decimal_separator": "comma",
            "char_delimiter": "doublequote",
            "number_lines_to_ignore": 0,
            "use_header": True,
        }
        serializer = CSVSourceSerializer(data=data)
        with self.assertRaises(KeyError):
            serializer.is_valid()
            self.assertEqual(len(serializer.errors), 2)

    def test_missing_lnglat_separator_and_field_info_raise_errors(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        data = {
            "file": [csv],
            "_type": "CSVSource",
            "name": "test",
            "encoding": "UTF-8",
            "coordinate_reference_system": "EPSG_4326",
            "coordinates_field": "one_column",
            "field_separator": "semicolon",
            "decimal_separator": "comma",
            "char_delimiter": "doublequote",
            "number_lines_to_ignore": 0,
            "use_header": True,
        }
        serializer = CSVSourceSerializer(data=data)
        with self.assertRaises(KeyError):
            serializer.is_valid()
            self.assertEqual(len(serializer.errors), 3)

    @patch(
        "project.geosource.serializers.CSVSource._get_records",
        side_effect=ValueError("ValueError mocked"),
    )
    def test_validate_fields_exceptions(self, get_record_mock):
        data = {
            "name": "soure-csv",
            "file": get_file("source.csv"),
            "_type": "CSVSource",
        }
        serializer = CSVSourceSerializer(data=data)

        with self.assertRaises(ValidationError):
            serializer._validate_field_infos(serializer.initial_data)


class GeoFileSourceSerializerTestCase(TestCase):
    @patch(
        "project.geosource.serializers.GeoFileSource._get_records",
        side_effect=ValueError("ValueError mocked"),
    )
    def test_validate_fields_infos_exceptions(self, get_record_mock):
        data = {
            "name": "source-geofile",
            "file": get_file("test.geojson"),
            "_type": "GeoFileSource",
        }
        serializer = GeoFileSourceSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer._validate_field_infos(serializer.initial_data)


class SourceSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.report = SourceReporting.objects.create()
        # Use GeoFileSource for easier testing purpose
        cls.source = GeoFileSource.objects.create(
            name="test-source",
            file=get_file("test.geojson"),
            geom_type=0,
            id_field="id",
            report=cls.report,
        )

    def test_update_method_reset_status(self):
        data = {
            "id": self.source.id,
            "name": "new-name",
            "_type": "GeoFileSource",
            "file": [get_file("test.geojson")],
            "fields": [],
        }
        serializer = SourceSerializer(data=data, partial=True)
        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )
        serializer.update(self.source, serializer.validated_data)

        self.source.refresh_from_db()
        self.report.refresh_from_db()
        self.assertEqual(self.source.status, Source.Status.NEED_SYNC.value)

    def test_backward_compatible_source_types(self):
        for old_type in ("GeoJSONSource", "ShapefileSource", "GeoPackageSource"):
            serializer_cls = SourceSerializer.get_serializer_from_type(old_type)
            self.assertEqual(serializer_cls, GeoFileSourceSerializer)

    def test_polymorphic_serializer_many(self):
        serializer = SourceSerializer(Source.objects.all(), many=True)
        self.assertIsInstance(serializer.data, list)
        self.assertGreater(len(serializer.data), 0)

    def test_polymorphic_create_subclass_serializer(self):
        ser = SourceSerializer()
        data = {
            "_type": "CommandSource",
            "name": "cmd_test_poly",
            "command": "test_command",
        }
        mock_source = MagicMock()
        with (
            patch.object(
                CommandSourceSerializer, "create", return_value=mock_source
            ) as mock_create,
            patch.object(SourceSerializer, "_update_fields", return_value=mock_source),
        ):
            instance = ser.create(data)
            self.assertEqual(instance, mock_source)
            mock_create.assert_called_once()

    def test_update_fields_validation_error_and_does_not_exist(self):
        Field.objects.create(source=self.source, name="id", label="ID")
        data = {
            "name": "new-name-2",
            "_type": "GeoFileSource",
            "file": [get_file("test.geojson")],
            "fields": [],
        }
        serializer = SourceSerializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with patch.object(SourceSerializer, "_update_fields", return_value=self.source):
            with patch.object(
                serializer,
                "get_initial",
                return_value={"fields": [{"name": "id", "label": ""}]},
            ):
                with self.assertRaises(ValidationError) as cm:
                    serializer.update(
                        self.source, {**serializer.validated_data, "fields": []}
                    )
                self.assertIn("Field configuration is not valid", str(cm.exception))

            with patch.object(
                serializer,
                "get_initial",
                return_value={"fields": [{"name": "does_not_exist", "label": "Valid"}]},
            ):
                res = serializer.update(
                    self.source, {**serializer.validated_data, "fields": []}
                )
                self.assertEqual(res, self.source)


class PostGISSourceSerializerTestCase(TestCase):
    @patch("psycopg2.connect")
    def test_first_record_and_get_connection(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1, "geom": "POINT(0 0)"}
        mock_connect.return_value.cursor.return_value = mock_cursor

        ser = PostGISSourceSerializer()
        data = {
            "db_username": "u",
            "db_password": "p",
            "db_host": "h",
            "db_port": 5432,
            "db_name": "d",
            "query": "SELECT * FROM test",
        }
        rec = ser._first_record(data)
        self.assertEqual(rec, {"id": 1, "geom": "POINT(0 0)"})

    def test_validate_geom_with_exception_in_non_geom_and_success(self):
        ser = PostGISSourceSerializer()
        with patch.object(
            ser, "_first_record", return_value={"id": 1, "geom": "POINT(0 0)"}
        ):
            data = {"geom_field": None, "geom_type": 0}
            result = ser._validate_geom(data)
            self.assertEqual(result["geom_field"], "geom")

    def test_validate_geom_missing_field_raises_error(self):
        ser = PostGISSourceSerializer()
        with patch.object(ser, "_first_record", return_value={"id": 1}):
            data = {"geom_field": "non_existent_geom", "geom_type": 1}
            with self.assertRaises(ValidationError) as cm:
                ser._validate_geom(data)
            self.assertIn("Field does not exist in source", str(cm.exception))

    def test_validate_query_connection_fails_raises_error(self):
        ser = PostGISSourceSerializer()
        with patch.object(
            ser, "_first_record", side_effect=Exception("DB connection failed")
        ):
            with self.assertRaises(ValidationError) as cm:
                ser._validate_query_connection({"query": "SELECT 1"})
            self.assertIn(
                "Connection informations or query are not valid", str(cm.exception)
            )


class FileSourceSerializerValidationTestCase(TestCase):
    def test_file_source_serializer_fields_without_file_returns_early(self):
        ser = GeoFileSourceSerializer()
        data = {"_type": "GeoFileSource", "fields": [{"name": "col"}], "file": None}
        self.assertIsNone(ser._validate_field_infos(data))

    def test_file_source_serializer_id_field_not_in_records_raises_validation_error(
        self,
    ):
        ser = GeoFileSourceSerializer()
        data = {
            "_type": "GeoFileSource",
            "name": "test_missing_id",
            "id_field": "non_existent_id",
            "file": get_file("test.geojson"),
        }
        with patch.object(
            GeoFileSource, "_get_records", return_value=([{"other": 1}], [], 1)
        ):
            with self.assertRaises(ValidationError) as cm:
                ser._validate_field_infos(data)
            self.assertIn("Can't find identifier field", str(cm.exception))


class WMTSSourceSerializerTestCase(TestCase):
    @patch("requests.get", side_effect=requests.ConnectionError("Connection refused"))
    def test_wmts_unreachable_raises_validation_error(self, mock_get):
        ser = WMTSSourceSerialize()
        data = {"url": "http://invalid-tile-server/{z}/{x}/{y}.png"}
        with self.assertRaises(ValidationError) as cm:
            ser.validate(data)
        self.assertIn("Can't reach specified tile server", str(cm.exception))


class CSVSourceSerializerExtraValidationTestCase(TestCase):
    def test_csv_serializer_to_representation_one_column(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"coords\n1,2")
        data = {
            "file": csv,
            "geom_type": 0,
            "name": "test_rep_one_col",
            "settings": {
                "coordinate_reference_system": "EPSG_4326",
                "field_separator": "semicolon",
                "decimal_separator": "point",
                "char_delimiter": "doublequote",
                "number_lines_to_ignore": 0,
                "use_header": True,
                "ignore_columns": False,
                "encoding": "UTF-8",
                "coordinates_field": "one_column",
                "coordinates_separator": "comma",
                "latlong_field": "coords",
                "coordinates_field_count": "xy",
            },
        }
        source = CSVSource.objects.create(**data)
        rep = CSVSourceSerializer(source).data
        self.assertNotIn("latitude_field", rep)
        self.assertNotIn("longitude_field", rep)

    def test_csv_validate_field_infos_without_file_returns_early(self):
        ser = CSVSourceSerializer()
        data = {"_type": "CSVSource", "fields": [{"name": "col"}], "file": None}
        self.assertIsNone(ser._validate_field_infos(data))

    def test_csv_validate_field_infos_missing_id_raises_validation_error(self):
        ser = CSVSourceSerializer()
        data = {
            "_type": "CSVSource",
            "name": "csv_missing_id",
            "id_field": "non_existent_id",
            "file": get_file("source.csv"),
        }
        with patch.object(
            CSVSource, "_get_records", return_value=([{"other": 1}], [], 1)
        ):
            with self.assertRaises(ValidationError) as cm:
                ser._validate_field_infos(data)
            self.assertIn("Can't find identifier field", str(cm.exception))

    def test_csv_validate_settings_combinations(self):
        ser = CSVSourceSerializer()
        base = {
            "_type": "CSVSource",
            "fields": [{"name": "col"}],
            "file": None,
        }

        # one_column missing latlong_field
        with self.assertRaises(ValidationError) as cm:
            ser.validate({**base, "settings": {"coordinates_field": "one_column"}})
        self.assertIn("latlong_field must be defined", str(cm.exception))

        # one_column missing coordinates_field_count
        with self.assertRaises(ValidationError) as cm:
            ser.validate(
                {
                    **base,
                    "settings": {
                        "coordinates_field": "one_column",
                        "latlong_field": "coord",
                    },
                }
            )
        self.assertIn("Coordinates order must be specified", str(cm.exception))

        # one_column missing coordinates_separator
        with self.assertRaises(ValidationError) as cm:
            ser.validate(
                {
                    **base,
                    "settings": {
                        "coordinates_field": "one_column",
                        "latlong_field": "coord",
                        "coordinates_field_count": "xy",
                    },
                }
            )
        self.assertIn("Coordinates separator must be specified", str(cm.exception))

        # two_columns missing latitude_field
        with self.assertRaises(ValidationError) as cm:
            ser.validate({**base, "settings": {"coordinates_field": "two_columns"}})
        self.assertIn("Latitude field must be specified", str(cm.exception))

        # two_columns missing longitude_field
        with self.assertRaises(ValidationError) as cm:
            ser.validate(
                {
                    **base,
                    "settings": {
                        "coordinates_field": "two_columns",
                        "latitude_field": "lat",
                    },
                }
            )
        self.assertIn("Longitude field must be specified", str(cm.exception))

        # invalid coordinates_field value
        with self.assertRaises(ValidationError) as cm:
            ser.validate({**base, "settings": {"coordinates_field": "three_columns"}})
        self.assertIn("Incorrect value for coordinates field", str(cm.exception))
