from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class SpriteValue(models.Model):
    """Sprite values provided to admin to use sprite icons in styles.
    These sprites should be included in any Base layer view."""

    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = _("Sprite icon")
        verbose_name_plural = _("Sprite icons")

    def __str__(self):
        return self.slug


class ExtraMenuItem(models.Model):
    """Extra menu items included in frontend."""

    label = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    href = models.CharField(max_length=255)
    icon = models.ImageField(upload_to="extra_menu_items/")
    limit_to_groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="extra_menu_items",
        help_text=_(
            "If defined, this extra menu item is only displayed to theses groups members."
        ),
    )

    class Meta:
        verbose_name = _("Extra menu item")
        verbose_name_plural = _("Extra menu items")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = slugify(self.label)
        return super().save(*args, **kwargs)
