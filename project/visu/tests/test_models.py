from django.test import TestCase

from project.visu.tests.factories import SpriteValueFactory


class SpriteValueTestCase(TestCase):
    def test_str(self):
        sprite_value = SpriteValueFactory()
        self.assertEqual(str(sprite_value), sprite_value.slug)
