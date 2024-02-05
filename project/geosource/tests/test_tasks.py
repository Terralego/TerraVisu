import logging
from datetime import datetime
from unittest import mock

from django.contrib.auth.models import Group
from django.test import TestCase
from geostore.models import Feature, Layer

from project.geosource.models import GeoJSONSource, GeometryTypes, SourceReporting
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

    def test_run_model_object_update_report(
        self, mock_index_feature, mock_es_delete, mock_es_create
    ):
        source = self.element
        source_report = SourceReporting.objects.create(
            status=SourceReporting.Status.PENDING.value,
        )
        source.report = source_report
        source.id = None
        source.save()

        self.assertIsNone(source.report.ended)
        run_model_object_method.apply(
            (
                source._meta.app_label,
                source._meta.model_name,
                source.pk,
                "refresh_data",
            )
        )
        source.report.refresh_from_db()
        self.assertIsInstance(source.report.message, str)
        self.assertIsInstance(source.report.ended, datetime)

    def test_set_failure_state_task_update_report(
        self,
        mock_index_feature,
        mock_es_delete,
        mock_es_create,
    ):
        logging.disable(logging.ERROR)
        source_report = SourceReporting.objects.create(
            status=SourceReporting.Status.PENDING.value,
        )
        source = GeoJSONSource.objects.create(
            name="exception-test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
            report=source_report,
        )

        self.assertIsNone(source.report.ended)
        try:
            run_model_object_method.apply(
                (
                    source._meta.app_label,
                    source._meta.model_name,
                    source.pk,
                    "method_that_does_not_exist",
                )
            )
        except AttributeError:
            source.report.refresh_from_db()
            self.assertIsInstance(source.report.message, str)
            self.assertIsInstance(source.report.ended, datetime)
            self.assertEqual(source.report.status, SourceReporting.Status.ERROR.value)

    def test_set_failure_state_task_when_report_status_none(
        self,
        mock_index_feature,
        mock_es_delete,
        mock_es_create,
    ):
        logging.disable(logging.ERROR)
        source_report = SourceReporting.objects.create(status=None)
        source = GeoJSONSource.objects.create(
            name="exception-test",
            geom_type=GeometryTypes.Point,
            file=get_file("test.geojson"),
            report=source_report,
        )

        self.assertIsNone(source.report.ended)
        try:
            run_model_object_method.apply(
                (
                    source._meta.app_label,
                    source._meta.model_name,
                    source.pk,
                    "method_that_does_not_exist",
                )
            )
        except AttributeError:
            source.report.refresh_from_db()
            self.assertEqual(source.report.status, SourceReporting.Status.ERROR.value)
