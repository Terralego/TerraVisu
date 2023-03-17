from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from project.geosource.models import PostGISSource
from project.terra_layer.models import Layer


@patch.object(Layer, "replace_source")
class UpdatePostgisSourceTestCase(TestCase):
    def setUp(self):
        self.source = PostGISSource.objects.create(
            name="test",
            db_name="test",
            db_password="test",
            db_host="localhost",
            geom_type=1,
            refresh=-1,
        )
        self.new_source = PostGISSource.objects.create(
            name="newtest",
            db_name="test",
            db_password="test",
            db_host="localhost",
            geom_type=1,
            refresh=-1,
        )
        self.layer = Layer.objects.create(
            source=self.source,
            name="layer_test",
            uuid="91c60192-9060-4bf6-b0de-818c5a362d89",
        )

    def test_replace_source_method_is_called(self, mocked_replace_source):
        call_command("update_postgis_source", self.layer.pk, self.new_source.name)
        # no fields matchs file and no dry-run option
        mocked_replace_source.assert_called_with(self.new_source, {}, False)

    def test_invalid_layer_does_not_call_replace_source_method(
        self, mocked_replace_source
    ):
        out = StringIO()
        call_command("update_postgis_source", 42, self.new_source.name, stdout=out)
        mocked_replace_source.assert_not_called()
