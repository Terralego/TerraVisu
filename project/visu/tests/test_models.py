from django.test import TestCase
from django.utils.text import slugify

from project.visu.tests.factories import ExtraMenuItemFactory, SpriteValueFactory


class SpriteValueTestCase(TestCase):
    def test_str(self):
        sprite_value = SpriteValueFactory()
        self.assertEqual(str(sprite_value), sprite_value.slug)


class ExtraMenuItemTestCase(TestCase):
    def test_str(self):
        extra_menu_item = ExtraMenuItemFactory()
        self.assertEqual(str(extra_menu_item), extra_menu_item.label)

    def test_save(self):
        extra_menu_item = ExtraMenuItemFactory()
        self.assertEqual(extra_menu_item.slug, slugify(extra_menu_item.label))

    def test_save_with_slug(self):
        extra_menu_item = ExtraMenuItemFactory(slug="test")
        self.assertEqual(extra_menu_item.slug, "test")
