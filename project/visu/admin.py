from admin_interface.admin import ThemeAdmin
from admin_interface.models import Theme
from constance.admin import Config, ConstanceAdmin
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from ordered_model.admin import (
    OrderedInlineModelAdminMixin,
    OrderedModelAdmin,
    OrderedTabularInline,
)

from project.admin import config_site
from project.geosource.models import Field, Source
from project.visu.forms import (
    ExtraSheetFieldInlineFormSet,
    SheetBlockAdminForm,
    SheetFieldInlineFormSet,
)
from project.visu.models import (
    ExtraMenuItem,
    ExtraSheetFieldThroughModel,
    FeatureSheet,
    SheetBlock,
    SheetField,
    SheetFieldThroughModel,
    SpriteValue,
)


@admin.register(ExtraMenuItem, site=config_site)
class ExtraMenuItemAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "href", "icon")


class ExtraSheetFieldTabularInline(OrderedTabularInline):
    model = ExtraSheetFieldThroughModel
    formset = ExtraSheetFieldInlineFormSet
    fields = (
        "extra_field",
        "order",
        "move_up_down_links",
    )
    readonly_fields = (
        "order",
        "move_up_down_links",
    )
    ordering = ("order",)
    extra = 1


class SheetFieldTabularInline(OrderedTabularInline):
    model = SheetFieldThroughModel
    formset = SheetFieldInlineFormSet
    fields = (
        "field",
        "order",
        "move_up_down_links",
    )
    readonly_fields = (
        "order",
        "move_up_down_links",
    )
    ordering = ("order",)
    extra = 1


@admin.register(FeatureSheet, site=config_site)
class FeatureSheetAdmin(admin.ModelAdmin):
    list_display = ("name", "get_sources")

    def get_sources(self, obj):
        return ", ".join([str(source) for source in obj.sources.all()])

    get_sources.short_description = _("Sources")


@admin.register(Field, site=config_site)
class FieldAdmin(admin.ModelAdmin):
    ordering = ["source", "order"]
    search_fields = ["name", "source"]

    def has_module_permission(self, request):
        # Do not display this in config page, it is only registered to
        # enable /autocomplete endpoint used in SheetFieldAdmin.
        return False


@admin.register(SheetField, site=config_site)
class SheetFieldAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "get_blocks",
        "type",
        "suffix",
        "decimals",
        "get_picto_true",
        "get_picto_false",
    )
    autocomplete_fields = ("field",)

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


@admin.register(Source, site=config_site)
class SourceAdmin(admin.ModelAdmin):
    # ordering = ["source", "order"]
    search_fields = ["name"]

    def has_module_permission(self, request):
        # Do not display this in config page, it is only registered to
        # enable /autocomplete endpoint used in SheetBlockAdmin.
        return False


@admin.register(SheetBlock, site=config_site)
class SheetBlockAdmin(OrderedInlineModelAdminMixin, OrderedModelAdmin):
    list_display = (
        "title",
        "get_sheet_name",
        "type",
        "get_fields_name",
        "display_title",
        "get_sources",
        "move_up_down_links",
    )
    inlines = (SheetFieldTabularInline, ExtraSheetFieldTabularInline)
    form = SheetBlockAdminForm
    autocomplete_fields = (
        "fields_source",
        "first_geom_source",
        "second_geom_source",
        "order_field",
    )

    class Media:
        js = ("admin/sheetblock_admin.js",)

    def get_sheet_name(self, obj):
        return obj.sheet.name

    get_sheet_name.short_description = _("Sheet")

    def get_fields_name(self, obj):
        return ", ".join(
            [field.label for field in obj.fields.all()]
            + [field.label for field in obj.extra_fields.all()]
        )

    get_fields_name.short_description = _("Fields")

    def get_sources(self, obj):
        sources = [obj.fields_source, obj.first_geom_source, obj.second_geom_source]
        return ", ".join([str(source) for source in sources if source is not None])

    get_sources.short_description = _("Sources")


config_site.register(SpriteValue)
admin.site.unregister([Config])
config_site.register([Config], ConstanceAdmin)
admin.site.unregister(Theme)
config_site.register(Theme, ThemeAdmin)
