from django.db import models
from django.utils.text import slugify


class SpriteValue(models.Model):
    """Sprite values provided to admin to use sprite icons in styles.
    These sprites should be included in any Base layer view."""

    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.slug


class ExtraMenuItem(models.Model):
    """Extra menu items included in frontend."""

    label = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    href = models.CharField(max_length=255)
    icon = models.ImageField(upload_to="extra_menu_items/")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = slugify(self.label)
        return super().save(*args, **kwargs)
