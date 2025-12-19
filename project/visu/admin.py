from admin_interface.admin import ThemeAdmin
from admin_interface.models import Theme
from constance.admin import Config, ConstanceAdmin
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from project.admin import config_site
from project.visu.models import (
    ExtraMenuItem,
    FeatureSheet,
    SheetBlock,
    SheetField,
    SpriteValue,
)


@admin.register(ExtraMenuItem, site=config_site)
class ExtraMenuItemAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "href", "icon")


@admin.register(FeatureSheet, site=config_site)
class FeatureSheetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "get_accessible_from",
    )

    def get_accessible_from(self, obj):
        return ", ".join([layer.name for layer in obj.accessible_from.all()])

    get_accessible_from.short_description = _("Accessible from")


@admin.register(SheetField, site=config_site)
class SheetFieldAdmin(admin.ModelAdmin):
    list_display = (
        "field",
        "get_blocks",
        "type",
        "suffix",
        "decimals",
        "get_picto_true",
        "get_picto_false",
    )

    class Media:
        js = ("admin/sheetfield_admin.js",)

    def get_picto_true(self, obj):
        return mark_safe(
            f'<img src="{obj.picto_true.url}"/>'
            if obj.picto_true
            else _("No pictogram")
        )

    get_picto_true.short_description = _("Pictogram for True values")

    def get_picto_false(self, obj):
        return mark_safe(
            f'<img src="{obj.picto_false.url}"/>'
            if obj.picto_false
            else _("No pictogram")
        )

    get_picto_false.short_description = _("Pictogram for False values")

    def get_blocks(self, obj):
        return ", ".join([block.title for block in obj.blocks.all()])

    get_blocks.short_description = _("Blocks")


@admin.register(SheetBlock, site=config_site)
class SheetBlockAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "get_sheet_name",
        "type",
        "display_title",
    )

    def get_sheet_name(self, obj):
        return obj.sheet.name

    get_sheet_name.short_description = _("Sheet")


config_site.register(SpriteValue)
admin.site.unregister([Config])
config_site.register([Config], ConstanceAdmin)
admin.site.unregister(Theme)
config_site.register(Theme, ThemeAdmin)
