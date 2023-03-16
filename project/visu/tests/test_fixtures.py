from django.core.management import call_command
from django.test import TestCase
from mapbox_baselayer.models import MapBaseLayer

from project.visu.models import SpriteValue


class TestFixtures(TestCase):
    def test_initial_data(self):
        call_command("loaddata", "/opt/terra-visu/project/fixtures/initial.json")
        self.assertTrue(SpriteValue.objects.exists())
        self.assertTrue(MapBaseLayer.objects.exists())
