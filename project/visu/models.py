from autoslug import AutoSlugField
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class SpriteValue(models.Model):
    """Sprite values provided to admin to use sprite icons in styles.
    These sprites should be included in any Base layer view."""

    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.slug


class ExtraMenuItem(models.Model):
    """Extra menu items included in frontend."""

    label = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(unique=True, populate_from="label")
    href = models.CharField(max_length=255)
    icon = models.ImageField(upload_to="extra_menu_items/")

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = _("Extra menu item")
        verbose_name_plural = _("Extra menu items")
