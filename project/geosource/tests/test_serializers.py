from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from project.geosource.models import CSVSource
from project.geosource.serializers import CSVSourceSerializer, GeoJSONSourceSerializer
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


class GeoJSONSourceSerializerTestCase(TestCase):
    @patch(
        "project.geosource.serializers.GeoJSONSource._get_records",
        side_effect=ValueError("ValueError mocked"),
    )
    def test_validate_fields_infos_exceptions(self, get_record_mock):
        data = {
            "name": "source-geojson",
            "file": get_file("test.geojson"),
            "_type": "GeoJSONSource",
        }
        serializer = GeoJSONSourceSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer._validate_field_infos(serializer.initial_data)
