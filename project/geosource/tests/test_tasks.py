import logging
from unittest import mock

from django.contrib.auth.models import Group
from django.test import TestCase
from geostore.models import Feature, Layer

from project.geosource.models import GeoJSONSource, GeometryTypes
from project.geosource.tasks import run_model_object_method
from project.geosource.tests.helpers import get_file


@mock.patch("elasticsearch.client.IndicesClient.create")
@mock.patch("elasticsearch.client.IndicesClient.delete")
@mock.patch("project.geosource.elasticsearch.index.LayerESIndex.index_feature")
class TaskTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(name="Group")
        cls.element = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
        )
        cls.element.groups.add(cls.group)

    def test_task_refresh_data_method(
        self, mocked_index_feature, mocked_es_delete, mocked_es_create
    ):
        run_model_object_method.apply(
            (
                self.element._meta.app_label,
                self.element._meta.model_name,
                self.element.pk,
                "refresh_data",
            )
        )
        self.assertEqual(Layer.objects.count(), 1)
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(Feature.objects.first().properties, {"id": 1, "test": 5})
        self.assertEqual(Layer.objects.first().authorized_groups.first().name, "Group")

    def test_task_refresh_data_method_wrong_pk(
        self, mocked_index_feature, mocked_es_delete, mocked_es_create
    ):
        logging.disable(logging.WARNING)
        run_model_object_method.apply(
            (
                self.element._meta.app_label,
                self.element._meta.model_name,
                99999,
                "refresh_data",
            )
        )
        self.assertEqual(Layer.objects.count(), 0)

    def test_task_wrong_method(
        self, mocked_index_feature, mocked_es_delete, mocked_es_create
    ):
        logging.disable(logging.ERROR)
        run_model_object_method.apply(
            (
                self.element._meta.app_label,
                self.element._meta.model_name,
                self.element.pk,
                "bad_method",
            )
        )
        self.assertEqual(Layer.objects.count(), 0)

    @mock.patch("project.geosource.models.Source.objects")
    def test_task_good_method_error(
        self, mock_source, mocked_index_feature, mocked_es_delete, mocked_es_create
    ):
        mock_source.get.side_effect = ValueError
        logging.disable(logging.ERROR)
        run_model_object_method.apply(
            (
                self.element._meta.app_label,
                self.element._meta.model_name,
                self.element.pk,
                "refresh_data",
            )
        )
        self.assertEqual(Layer.objects.count(), 0)
