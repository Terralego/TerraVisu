from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from project.geosource.models import Field
from project.terra_layer.models import Layer


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


class SheetFieldType(models.TextChoices):
    BOOLEAN = "BOOLEAN", _("Boolean")
    TEXTUAL = "TEXTUAL", _("Textual")
    NUMERICAL = "NUMERICAL", _("Numerical")


class SheetBlockType(models.TextChoices):
    FIELDS = "FIELDS", _("Fields")
    BOOLEANS = "BOOLEANS", _("Booleans")
    FIELDS_TABLE = "FIELDS_TABLE", _("Fields table")
    TEXT = "TEXT", _("Text")
    PANORAMAX = "PANORAMAX", _("Panoramax")
    MAP = "MAP", _("Map")
    RADAR_PLOT = "RADAR_PLOT", _("Radar plot")
    BAR_PLOT = "BAR_PLOT", _("Bars plot")
    DISTRIB_PLOT = "DISTRIB_PLOT", _("Distribution plot")


class FeatureSheet(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Sheet name"))
    unique_identifier = models.ForeignKey(
        Field, on_delete=models.CASCADE, verbose_name=_("Unique identifier")
    )
    accessible_from = models.ManyToManyField(Layer, verbose_name=_("Accessible from"))

    class Meta:
        verbose_name = _("Feature sheet")
        verbose_name_plural = _("Feature sheets")

    def __str__(self):
        return self.name


class SheetField(models.Model):  # OrderedModel
    field = models.ForeignKey(
        Field, on_delete=models.CASCADE, verbose_name=_("Source field")
    )
    # label : field.label ?
    # source : field.source
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=9,
        choices=SheetFieldType.choices,
        default=SheetFieldType.TEXTUAL,
        verbose_name=_("Sheet field type"),
    )
    suffix = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Suffix"),
    )
    decimals = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Decimals")
    )
    picto_true = models.FileField(
        upload_to="sheet_files",
        null=True,
        blank=True,
        verbose_name=_("Pictogram for True values"),
        validators=[],
    )
    picto_false = models.FileField(
        upload_to="sheet_files",
        null=True,
        blank=True,
        verbose_name=_("Pictogram for False values"),
    )

    class Meta:
        verbose_name = _("Sheet field")
        verbose_name_plural = _("Sheet fields")
        # Ordering

    def __str__(self):
        return self.field.label


class SheetBlock(models.Model):  # OrderedModel
    title = models.CharField(max_length=255, verbose_name=_("Block title"))
    display_title = models.BooleanField(default=True, verbose_name=_("Display title"))
    type = models.CharField(
        max_length=12,
        choices=SheetBlockType.choices,
        default=SheetBlockType.TEXT,
        verbose_name=_("Sheet block type"),
    )
    sheet = models.ForeignKey(
        FeatureSheet,
        on_delete=models.CASCADE,
        verbose_name=_("Sheet"),
        related_name="blocks",
    )
    # settings : listes de fields...
    fields = models.ManyToManyField(
        SheetField, verbose_name=_("Sheet fields"), related_name="blocks"
    )
    text = models.TextField(
        blank=True,
        verbose_name=_("Text"),
    )
    # geom_field = models.ForeignKey(
    #     SheetField,
    #     verbose_name=_("Geom fields"),
    # )

    class Meta:
        verbose_name = _("Sheet block")
        verbose_name_plural = _("Sheet blocks")
        # ordering

    def __str__(self):
        return self.title
