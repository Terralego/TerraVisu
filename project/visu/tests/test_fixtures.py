from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from mapbox_baselayer.models import MapBaseLayer


class TestFixtures(TestCase):
    def test_initial_data(self):
        out = StringIO()
        call_command(
            "loaddata",
            "/opt/terra-visu/project/fixtures/initial.json",
            stdout=out,
        )
        self.assertTrue(MapBaseLayer.objects.exists())
