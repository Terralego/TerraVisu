import logging
import os
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from django.urls import reverse
from project.geosource.models import (
    CommandSource,
    Field,
    FieldTypes,
    GeoJSONSource,
    GeometryTypes,
    PostGISSource,
    ShapefileSource,
    Source,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.test import APIClient

UserModel = get_user_model()


class ModelSourceViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.default_user = UserModel.objects.get_or_create(
            is_superuser=True, **{UserModel.USERNAME_FIELD: "testuser"}
        )[0]
        self.client.force_authenticate(self.default_user)
        self.source_geojson = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
        )
        self.source_example = {
            "_type": "PostGISSource",
            "name": "Test Source",
            "db_username": "username",
            "db_name": "dbname",
            "db_host": "hostname.com",
            "query": "SELECT 1",
            "geom_field": "geom",
            "refresh": -1,
            "geom_type": GeometryTypes.LineString.value,
        }

    def test_wrong_type_source_creation(self):
        self.source_example["_type"] = "WrongSource"
        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**self.source_example, "db_password": "test_password"},
            format="json",
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            {"_type": "WrongSource's type is unknown"},
            response.json(),
        )

    def test_list_view(self):
        # Create many sources and list them
        [
            PostGISSource.objects.create(
                name=f"test-{x}", refresh=-1, geom_type=GeometryTypes.LineString.value
            )
            for x in range(5)
        ]

        response = self.client.get(reverse("geosource:geosource-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(Source.objects.count(), len(response.json()))

    def test_refresh_view_fail(self):
        with patch(
            "project.geosource.mixins.CeleryCallMethodsMixin.run_async_method",
            return_value=False,
        ):
            response = self.client.get(
                reverse("geosource:geosource-refresh", args=[self.source_geojson.pk])
            )
        self.assertEqual(response.status_code, HTTP_500_INTERNAL_SERVER_ERROR)

    def test_refresh_view_accepted(self):
        with patch(
            "project.geosource.mixins.CeleryCallMethodsMixin.run_async_method",
            return_value=True,
        ):
            response = self.client.get(
                reverse("geosource:geosource-refresh", args=[self.source_geojson.pk])
            )
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)

    @patch(
        "project.geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "project.geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("project.geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_postgis_source_creation(self):
        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**self.source_example, "db_password": "test_password"},
            format="json",
        )

        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertDictContainsSubset(self.source_example, response.json())

    @patch(
        "project.geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "project.geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("project.geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_postgis_source_creation_no_geom_field_wrong_geom(self):
        self.source_example["geom_field"] = None
        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**self.source_example, "db_password": "test_password"},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            {"non_field_errors": ["No geom field found of type LineString"]},
            response.json(),
        )

    @patch(
        "project.geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"foo": GEOSGeometry("LINESTRING (0 0, 1 1)")}),
    )
    @patch(
        "project.geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("project.geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_postgis_source_creation_no_geom_field_good_geom(self):
        self.source_example["geom_field"] = None
        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**self.source_example, "db_password": "test_password"},
            format="json",
        )
        self.source_example["geom_field"] = "foo"
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertDictContainsSubset(self.source_example, response.json())

    def test_wmts_source_creation(self):

        wmts_source = {
            "_type": "WMTSSource",
            "name": "Test Source",
            "url": "http://fakeurl.com/",
            "tile_size": 256,
        }

        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**wmts_source},
            format="json",
        )

        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertDictContainsSubset(wmts_source, response.json())

    @patch(
        "project.geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "project.geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("project.geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_update_fields(self):
        self.source_example["name"] = "Test Update Source"
        self.source_example.pop("_type", None)
        source = PostGISSource.objects.create(**self.source_example)
        field = Field.objects.create(
            source=source,
            name="field_name",
            label="Label",
            data_type=FieldTypes.String.value,
        )

        response = self.client.get(
            reverse("geosource:geosource-detail", args=[source.pk])
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        test_field_label = "New Test Label"

        source_json = response.json()
        source_json["fields"][0]["label"] = test_field_label

        update_response = self.client.patch(
            reverse("geosource:geosource-detail", args=[source.pk]), source_json
        )

        self.assertEqual(update_response.status_code, HTTP_200_OK)
        self.assertEqual(
            update_response.json().get("fields")[0]["label"], test_field_label
        )

        field.refresh_from_db()
        self.assertEqual(field.label, test_field_label)

    @patch(
        "project.geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "project.geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("project.geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_update_fields_fail_from_source(self):
        def run_sync_method_result(cmd, success_state):
            value = MagicMock()
            value.result = False
            return value

        self.source_example["name"] = "Test Update Source"
        self.source_example.pop("_type", None)
        source = PostGISSource.objects.create(**self.source_example)
        Field.objects.create(
            source=source,
            name="field_name",
            label="Label",
            data_type=FieldTypes.String.value,
        )
        response = self.client.get(
            reverse("geosource:geosource-detail", args=[source.pk])
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        test_field_label = "New Test Label"

        source_json = response.json()
        source_json["fields"][0]["label"] = test_field_label
        with patch(
            "project.geosource.mixins.CeleryCallMethodsMixin.run_sync_method",
            side_effect=run_sync_method_result,
        ):
            update_response = self.client.patch(
                reverse("geosource:geosource-detail", args=[source.pk]), source_json
            )
        self.assertEqual(update_response.status_code, HTTP_400_BAD_REQUEST)

    @patch(
        "project.geosource.models.Source._get_records",
        MagicMock(
            return_value=[
                {"a": "b", "c": 42, "d": b"4", "e": b"\xe8", "_geom_": "POINT(0 0)"}
            ]
        ),
    )
    def test_update_fields_method(self):
        logging.disable(logging.WARNING)
        obj = Source.objects.create(geom_type=10)
        obj.update_fields()

        self.assertEqual(FieldTypes.String.value, obj.fields.get(name="a").data_type)
        self.assertEqual(FieldTypes.Integer.value, obj.fields.get(name="c").data_type)
        self.assertEqual(FieldTypes.Undefined.value, obj.fields.get(name="d").data_type)

    @patch(
        "project.geosource.models.Source._get_records",
        MagicMock(return_value=[{"a": "b", "c": 42, "_geom_": "POINT(0 0)"}]),
    )
    def test_update_fields_with_delete_method(self):
        obj = Source.objects.create(geom_type=10)
        Field.objects.create(
            source=obj,
            name="field_name",
            label="Label",
            data_type=FieldTypes.String.value,
        )
        obj.update_fields()

        self.assertEqual(FieldTypes.String.value, obj.fields.get(name="a").data_type)
        self.assertEqual(FieldTypes.Integer.value, obj.fields.get(name="c").data_type)
        self.assertEqual(0, Field.objects.filter(name="field_name").count())

    def test_ordering_filtering_search(self):
        self.source_geojson.delete()

        obj = GeoJSONSource.objects.create(
            name="foo",
            geom_type=GeometryTypes.Point.value,
        )
        obj2 = CommandSource.objects.create(
            name="bar",
            geom_type=GeometryTypes.LineString.value,
        )
        ShapefileSource.objects.create(
            name="baz",
            geom_type=GeometryTypes.Polygon.value,
        )

        list_url = reverse("geosource:geosource-list")
        response = self.client.get(list_url)
        data = response.json()
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(data), 3)
        self.assertEqual(response.json()[0]["name"], obj.name)

        # Test ordering
        response = self.client.get(list_url, {"ordering": "name"})
        self.assertEqual(response.json()[-1]["name"], obj.name)

        response = self.client.get(list_url, {"ordering": "-name"})
        self.assertEqual(response.json()[0]["name"], obj.name)

        response = self.client.get(list_url, {"ordering": "polymorphic_ctype__model"})
        self.assertEqual(response.json()[0]["name"], obj2.name)

        response = self.client.get(list_url, {"ordering": "-polymorphic_ctype__model"})
        self.assertEqual(response.json()[-1]["name"], obj2.name)

        # Test filter
        response = self.client.get(list_url, {"geom_type": GeometryTypes.Point.value})
        data = response.json()
        self.assertEqual(len(data), 1, data)
        self.assertEqual(data[0]["name"], obj.name)

        # Test search
        response = self.client.get(list_url, {"search": "foo"})

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], obj.name)

        response = self.client.get(list_url, {"search": "bar"})

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], obj2.name)

    def test_property_values(self):
        source = GeoJSONSource.objects.create(
            name="foo",
            geom_type=GeometryTypes.Point.value,
        )

        class FakeLayer:
            def get_property_values(self, property):
                return ["fake", "list"]

        with patch(
            "project.geosource.geostore_callbacks.layer_callback",
            MagicMock(return_value=FakeLayer()),
        ):
            response = self.client.get(
                reverse(
                    "geosource:geosource-property-values",
                    args=[
                        source.pk,
                    ],
                ),
                {"property": "country"},
            )
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), ["fake", "list"])

            response = self.client.get(
                reverse(
                    "geosource:geosource-property-values",
                    args=[
                        source.pk,
                    ],
                ),
            )
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
