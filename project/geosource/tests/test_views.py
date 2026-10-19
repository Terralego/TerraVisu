import io
import zipfile
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.gdal import DataSource, SpatialReference
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from geostore import GeometryTypes
from rest_framework import status
from rest_framework.test import APITestCase

from project.geosource.models import (
    Field,
    FieldTypes,
    GeoFileSource,
    PostGISSource,
    SourceReporting,
)
from project.geosource.tests.helpers import get_file
from project.geosource.views import (
    SourceModelViewset,
    _detect_geojson_geometry_types,
    _detect_geometry_types,
    _geom_type_id,
    _preview_bool_fields,
)

UserModel = get_user_model()


class FilePreviewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.default_user = UserModel.objects.create(
            is_superuser=True, **{UserModel.USERNAME_FIELD: "testuser"}
        )
        cls.preview_url = reverse("geosource:geosource-file-preview")

    def setUp(self):
        self.client.force_authenticate(self.default_user)

    def test_file_preview_without_file_returns_400(self):
        response = self.client.post(self.preview_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"error": "No file provided"})

    def test_file_preview_geojson_success(self):
        file = get_file("test.geojson")
        response = self.client.post(
            self.preview_url, {"file": file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["geometry_type_name"], "Point")
        self.assertEqual(data["geometry_type"], GeometryTypes.Point.value)
        self.assertEqual(data["crs"], "EPSG:4326")
        self.assertIn("features", data)
        self.assertIn("fields", data)
        self.assertGreater(data["file_size"], 0)
        self.assertIsNotNone(data["bbox"])

    def test_file_preview_zipped_shapefile_success(self):
        file = get_file("test.zip")
        response = self.client.post(
            self.preview_url, {"file": file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["geometry_type_name"], "Polygon")
        self.assertEqual(data["geometry_type"], GeometryTypes.Polygon.value)
        self.assertIn("NOM", [f["name"] for f in data["fields"]])
        self.assertGreater(len(data["features"]), 0)

    def test_file_preview_gpkg_default_layer_success(self):
        file = get_file("test.gpkg")
        response = self.client.post(
            self.preview_url, {"file": file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["geometry_type_name"], "Point")
        self.assertIn("features", data)

    def test_file_preview_gpkg_specific_layer_success(self):
        file = get_file("test.gpkg")
        response = self.client.post(
            self.preview_url,
            {"file": file, "layer_name": "layer_two"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["geometry_type_name"], "Point")

    def test_file_preview_csv_two_columns_coordinates(self):
        file = get_file("source.csv")
        response = self.client.post(
            self.preview_url,
            {
                "file": file,
                "field_separator": "semicolon",
                "char_delimiter": "doublequote",
                "decimal_separator": "point",
                "use_header": "true",
                "coordinates_field": "two_columns",
                "latitude_field": "YCOORD",
                "longitude_field": "XCOORD",
                "coordinate_reference_system": "EPSG_2154",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["crs"], "EPSG:2154")
        self.assertIsNotNone(data["bbox"])
        self.assertEqual(data["record_count"], 6)
        self.assertIn("XCOORD", [f["name"] for f in data["fields"]])

    def test_file_preview_csv_one_column_coordinates(self):
        file = get_file("source_xy.csv")
        response = self.client.post(
            self.preview_url,
            {
                "file": file,
                "field_separator": "semicolon",
                "coordinates_field": "one_column",
                "latlong_field": "coordxy",
                "coordinates_field_count": "xy",
                "coordinates_separator": "comma",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNotNone(data["bbox"])
        self.assertEqual(data["record_count"], 9)

    def test_file_preview_csv_ignore_lines_and_invalid_srs(self):
        file = get_file("source.csv")
        response = self.client.post(
            self.preview_url,
            {
                "file": file,
                "field_separator": "semicolon",
                "number_lines_to_ignore": 1,
                "use_header": "false",
                "coordinate_reference_system": "INVALID_SRS",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["record_count"], 6)
        self.assertIsNone(data["crs"])

    def test_file_preview_csv_two_columns_invalid_column_name(self):
        file = get_file("source.csv")
        response = self.client.post(
            self.preview_url,
            {
                "file": file,
                "field_separator": "semicolon",
                "coordinates_field": "two_columns",
                "latitude_field": "NON_EXISTENT_LAT",
                "longitude_field": "NON_EXISTENT_LNG",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data["bbox"])

    def test_file_preview_csv_one_column_invalid_column_name(self):
        file = get_file("source_xy.csv")
        response = self.client.post(
            self.preview_url,
            {
                "file": file,
                "field_separator": "semicolon",
                "coordinates_field": "one_column",
                "latlong_field": "NON_EXISTENT_COL",
                "coordinates_field_count": "xy",
                "coordinates_separator": "comma",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data["bbox"])

    def test_file_preview_csv_one_column_yx_order_and_comma_decimal(self):
        csv_content = b"coords;name\n48,8566 2,3522;Paris\n45,7640 4,8357;Lyon\n"
        csv_file = SimpleUploadedFile(
            "cities.csv", csv_content, content_type="text/csv"
        )
        response = self.client.post(
            self.preview_url,
            {
                "file": csv_file,
                "field_separator": "semicolon",
                "decimal_separator": "comma",
                "coordinates_field": "one_column",
                "latlong_field": "coords",
                "coordinates_field_count": "yx",
                "coordinates_separator": "space",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNotNone(data["bbox"])
        self.assertEqual(data["record_count"], 2)

    def test_file_preview_csv_type_detection_bool_and_float(self):
        csv_content = b"label;active;score\nA;true;12,5\nB;false;18,2\n"
        csv_file = SimpleUploadedFile("data.csv", csv_content, content_type="text/csv")
        response = self.client.post(
            self.preview_url,
            {
                "file": csv_file,
                "field_separator": "semicolon",
                "decimal_separator": "comma",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        field_types = {f["name"]: f["type"] for f in data["fields"]}
        self.assertEqual(field_types.get("active"), "boolean")
        self.assertEqual(field_types.get("score"), "float")

    def test_file_preview_csv_without_headers(self):
        file = get_file("source_noheader.csv")
        response = self.client.post(
            self.preview_url,
            {
                "file": file,
                "field_separator": "semicolon",
                "use_header": "false",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(all(f["name"].startswith("Col_") for f in data["fields"]))

    def test_file_preview_csv_empty_file(self):
        file = get_file("source_empty.csv")
        response = self.client.post(
            self.preview_url,
            {"file": file, "field_separator": "semicolon"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["record_count"], 0)

    def test_file_preview_unsupported_file_returns_400(self):
        invalid_file = SimpleUploadedFile(
            "test.xyz", b"not a valid vector data format", content_type="text/plain"
        )
        response = self.client.post(
            self.preview_url, {"file": invalid_file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unsupported file type", response.json()["error"])

    def test_file_preview_invalid_zip_archive_returns_400(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            z.writestr("test.txt", "not a shp")
        zip_buffer.seek(0)
        invalid_zip = SimpleUploadedFile("empty.zip", zip_buffer.read())

        response = self.client.post(
            self.preview_url, {"file": invalid_zip}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No .shp file found in archive", response.json()["error"])

    @patch("project.geosource.views.is_zipfile", return_value=False)
    @patch("project.geosource.views.DataSource")
    def test_file_preview_unzipped_shapefile(self, mock_ds, mock_is_zipfile):
        mock_layer = MagicMock()
        mock_layer.name = "test"
        mock_layer.geom_type.name = "Polygon"
        mock_layer.fields = ["name"]
        mock_layer.field_types = []
        mock_layer.num_feat = 1
        mock_layer.srs = None
        mock_layer.extent = None
        mock_layer.__iter__.return_value = []
        mock_ds.return_value = [mock_layer]

        shp_file = SimpleUploadedFile("test.shp", b"dummy shp")
        response = self.client.post(
            self.preview_url, {"file": shp_file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GpkgLayersAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.default_user = UserModel.objects.create(
            is_superuser=True, **{UserModel.USERNAME_FIELD: "testuser_gpkg"}
        )
        cls.layers_url = reverse("geosource:geosource-gpkg-layers")

    def setUp(self):
        self.client.force_authenticate(self.default_user)

    def test_gpkg_layers_without_file_returns_400(self):
        response = self.client.post(self.layers_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"error": "No file provided"})

    def test_gpkg_layers_invalid_file_returns_400(self):
        invalid_file = SimpleUploadedFile("invalid.gpkg", b"not a sqlite db")
        response = self.client.post(
            self.layers_url, {"file": invalid_file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid GPKG file", response.json()["error"])

    def test_gpkg_layers_valid_gpkg_returns_layer_list(self):
        file = get_file("test.gpkg")
        response = self.client.post(self.layers_url, {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        layers = response.json().get("layers", [])
        layer_names = [info["name"] for info in layers]
        self.assertIn("test", layer_names)
        self.assertIn("layer_two", layer_names)


class FilePreviewSavedAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.default_user = UserModel.objects.create(
            is_superuser=True, **{UserModel.USERNAME_FIELD: "testuser_saved"}
        )

    def setUp(self):
        self.client.force_authenticate(self.default_user)

    def test_file_preview_saved_geofile_success(self):
        source = GeoFileSource.objects.create(
            name="preview_saved_source",
            geom_type=GeometryTypes.Point.value,
            file=get_file("test.geojson"),
        )
        report = SourceReporting.objects.create(added_lines=15)
        source.report = report
        source.save()

        Field.objects.create(
            source=source,
            name="city",
            data_type=FieldTypes.String.value,
            sample=["Paris", "Lyon"],
            order=0,
        )
        Field.objects.create(
            source=source,
            name="population",
            data_type=FieldTypes.Integer.value,
            sample=[2000000, 500000],
            order=1,
        )

        url = reverse("geosource:geosource-file-preview-saved", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["record_count"], 15)
        self.assertEqual(data["geometry_type_name"], "Point")
        self.assertEqual(len(data["fields"]), 2)
        self.assertEqual(data["fields"][0]["name"], "city")
        self.assertEqual(data["fields"][0]["type"], "str")
        self.assertEqual(data["fields"][1]["name"], "population")
        self.assertEqual(data["fields"][1]["type"], "int")
        self.assertEqual(len(data["features"]), 2)
        self.assertEqual(data["features"][0]["city"], "Paris")
        self.assertEqual(data["features"][0]["population"], 2000000)

    def test_file_preview_saved_with_original_srid(self):
        source = GeoFileSource.objects.create(
            name="preview_srid_source",
            geom_type=GeometryTypes.Point.value,
            original_srid=2154,
            file=get_file("test.geojson"),
        )
        url = reverse("geosource:geosource-file-preview-saved", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("original : EPSG:2154", data["crs"])

    def test_file_preview_saved_fallback_to_file_bbox(self):
        source = GeoFileSource.objects.create(
            name="preview_fallback_source",
            geom_type=None,
            file=get_file("test.geojson"),
        )
        url = reverse("geosource:geosource-file-preview-saved", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNotNone(data["bbox"])

    @patch("project.geosource.views.DataSource")
    def test_file_preview_saved_fallback_reprojects_file_bbox(self, mock_ds):
        source = GeoFileSource.objects.create(
            name="preview_fallback_reproject",
            geom_type=None,
            file=get_file("test.geojson"),
        )
        mock_layer = MagicMock()
        mock_layer.extent = MagicMock(
            min_x=930000, max_x=940000, min_y=6920000, max_y=6930000
        )
        mock_layer.srs = SpatialReference(2154)
        mock_ds.return_value = [mock_layer]

        url = reverse("geosource:geosource-file-preview-saved", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNotNone(data["bbox"])

    def test_file_preview_saved_record_count_from_report_total(self):
        source = GeoFileSource.objects.create(
            name="preview_resynced_source",
            geom_type=GeometryTypes.Point.value,
            file=get_file("test.geojson"),
        )
        source.report = SourceReporting.objects.create(
            added_lines=0, modified_lines=20, total=20
        )
        source.save()

        url = reverse("geosource:geosource-file-preview-saved", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["record_count"], 20)

    def test_file_preview_saved_record_count_without_report(self):
        source = GeoFileSource.objects.create(
            name="preview_unsynced_source",
            geom_type=GeometryTypes.Point.value,
            file=get_file("test.geojson"),
        )

        url = reverse("geosource:geosource-file-preview-saved", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["record_count"], 1)


class DownloadAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.default_user = UserModel.objects.create(
            is_superuser=True, **{UserModel.USERNAME_FIELD: "testuser_download"}
        )

    def setUp(self):
        self.client.force_authenticate(self.default_user)

    def test_download_geofile_success(self):
        source = GeoFileSource.objects.create(
            name="download_source",
            geom_type=GeometryTypes.Point.value,
            file=get_file("test.geojson"),
        )
        url = reverse("geosource:geosource-download", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/geo+json")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        self.assertGreater(len(response.getvalue()), 0)

    def test_download_source_without_file_returns_404(self):
        source = PostGISSource.objects.create(
            name="postgis_download",
            geom_type=GeometryTypes.Point.value,
        )
        url = reverse("geosource:geosource-download", args=[source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ViewsHelperFunctionsTestCase(APITestCase):
    def test_geom_type_id_valid_and_invalid(self):
        self.assertEqual(_geom_type_id("Point"), GeometryTypes.Point.value)
        self.assertEqual(_geom_type_id("Polygon"), GeometryTypes.Polygon.value)
        self.assertIsNone(_geom_type_id("NonExistentType"))

    def test_detect_geometry_types(self):
        file_path = str(
            settings.BASE_DIR / "geosource" / "tests" / "data" / "test.gpkg"
        )
        types = _detect_geometry_types(file_path, "test")
        self.assertIn("Point", types)

    def test_detect_geometry_types_failure_returns_empty_set(self):
        types = _detect_geometry_types("/non/existent/path.gpkg", "layer")
        self.assertEqual(types, set())

    def test_detect_geojson_geometry_types(self):
        file_path = str(
            settings.BASE_DIR / "geosource" / "tests" / "data" / "test.geojson"
        )
        types = _detect_geojson_geometry_types(file_path)
        self.assertEqual(types, {"Point"})

    def test_detect_geojson_geometry_types_error_returns_empty_set(self):
        types = _detect_geojson_geometry_types("/non/existent/path.geojson")
        self.assertEqual(types, set())

    def test_preview_bool_fields_detection_from_features(self):
        file_path = str(
            settings.BASE_DIR / "geosource" / "tests" / "data" / "test.geojson"
        )
        ds = DataSource(file_path)
        layer = ds[0]
        # mock field types to simulate OFTInteger
        fake_type = MagicMock()
        fake_type.__name__ = "OFTInteger"
        with patch.object(type(layer), "field_types", [fake_type]):
            with patch.object(type(layer), "fields", ["is_active"]):
                features = [{"is_active": 0}, {"is_active": 1}]
                bool_fields = _preview_bool_fields(layer, features, None, is_gpkg=False)
                self.assertIn("is_active", bool_fields)

    def test_extract_layer_data_mixed_geometries_detection(self):
        mock_layer = MagicMock()
        mock_layer.geom_type.name = "Unknown"
        mock_layer.fields = []
        mock_layer.field_types = []
        mock_layer.num_feat = 2
        mock_layer.srs = None
        mock_layer.extent = None
        mock_layer.__iter__.return_value = []

        viewset = SourceModelViewset()
        with patch(
            "project.geosource.views._detect_geojson_geometry_types",
            return_value={"Point", "Polygon"},
        ):
            result = viewset._extract_layer_data(
                mock_layer, file_path="dummy.geojson", is_geojson=True
            )
            self.assertTrue(result["mixed_geometries"])
            self.assertEqual(result["geometry_types"], ["Point", "Polygon"])

    def test_extract_layer_data_reprojects_bbox_for_non_4326(self):
        mock_layer = MagicMock()
        mock_layer.fields = []
        mock_layer.field_types = []
        mock_layer.num_feat = 1
        mock_layer.geom_type.name = "Point"
        mock_layer.extent = MagicMock(
            min_x=930000, max_x=940000, min_y=6920000, max_y=6930000
        )
        mock_layer.srs = SpatialReference(2154)
        mock_layer.__iter__.return_value = []

        viewset = SourceModelViewset()
        result = viewset._extract_layer_data(mock_layer)
        self.assertIsNotNone(result["bbox"])
        self.assertEqual(result["crs"], "EPSG:2154")
