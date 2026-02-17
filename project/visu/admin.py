from admin_interface.admin import ThemeAdmin
from admin_interface.models import Theme
from constance.admin import Config, ConstanceAdmin
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from ordered_model.admin import (
    OrderedInlineModelAdminMixin,
    OrderedModelAdmin,
    OrderedTabularInline,
)

from project.admin import config_site
from project.geosource.models import Field
from project.visu.models import (
    ExtraMenuItem,
    ExtraSheetFieldThroughModel,
    FeatureSheet,
    SheetBlock,
    SheetBlockType,
    SheetField,
    SheetFieldThroughModel,
    SheetFieldType,
    SpriteValue,
)


@admin.register(ExtraMenuItem, site=config_site)
class ExtraMenuItemAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "href", "icon")


class SheetFieldTabularInline(OrderedTabularInline):
    model = SheetFieldThroughModel
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


class ExtraSheetFieldTabularInline(OrderedTabularInline):
    model = ExtraSheetFieldThroughModel
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


class SheetBlockAdminForm(ModelForm):
    class Meta:
        model = SheetBlock
        fields = (
            "sheet",
            "title",
            "display_title",
            "type",
            "fields",
            "extra_fields",
            "text",
            "geom_field",
        )

    def clean(self):
        cleaned_data = super().clean()
        block_type = cleaned_data.get("type")
        fields = cleaned_data.get("fields", []) + cleaned_data.get("extra_fields", [])

        if block_type in [
            SheetBlockType.RADAR_PLOT,
            SheetBlockType.BAR_PLOT,
            SheetBlockType.DISTRIB_PLOT,
        ]:
            non_numerical = [f for f in fields if f.type != SheetFieldType.NUMERICAL]
            if non_numerical:
                field_names = ", ".join([f.label for f in non_numerical])
                raise ValidationError(
                    _(
                        "Block type '%(block_type)s' requires all fields to be NUMERICAL. The following fields are not numerical: %(field_names)s"
                    )
                    % {
                        "block_type": dict(SheetBlockType.choices)[block_type],
                        "field_names": field_names,
                    }
                )

        elif block_type == SheetBlockType.BOOLEANS:
            non_boolean = [f for f in fields if f.type != SheetFieldType.BOOLEAN]
            if non_boolean:
                field_names = ", ".join([f.label for f in non_boolean])
                raise ValidationError(
                    _(
                        "Block type 'Booleans' requires all fields to be BOOLEAN. The following fields are not boolean: %(field_names)s"
                    )
                    % {"field_names": field_names}
                )
        return cleaned_data


@admin.register(FeatureSheet, site=config_site)
class FeatureSheetAdmin(admin.ModelAdmin):
    list_display = ("name", "get_accessible_from")

    def get_accessible_from(self, obj):
        return ", ".join([layer.name for layer in obj.accessible_from.all()])

    get_accessible_from.short_description = _("Accessible from")


@admin.register(Field, site=config_site)
class FieldAdmin(admin.ModelAdmin):
    ordering = ["source", "order"]
    search_fields = ["name"]

    def has_module_permission(self, request):
        # Do not display this in the Admin, it is only registered to
        # enable the /autocomplete endpoint used in SheetFieldAdmin.
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


@admin.register(SheetBlock, site=config_site)
class SheetBlockAdmin(OrderedInlineModelAdminMixin, OrderedModelAdmin):
    list_display = (
        "title",
        "get_sheet_name",
        "type",
        "get_fields_name",
        "display_title",
        "move_up_down_links",
    )
    inlines = (SheetFieldTabularInline, ExtraSheetFieldTabularInline)
    form = SheetBlockAdminForm

    class Media:
        js = ("admin/sheetblock_admin.js",)

    def get_sheet_name(self, obj):
        return obj.sheet.name

    get_sheet_name.short_description = _("Sheet")

    def get_fields_name(self, obj):
        return ", ".join(
            [str(field) for field in obj.fields.all()]
            + [str(field) for field in obj.extra_fields.all()]
        )

    get_fields_name.short_description = _("Fields")


config_site.register(SpriteValue)
admin.site.unregister([Config])
config_site.register([Config], ConstanceAdmin)
admin.site.unregister(Theme)
config_site.register(Theme, ThemeAdmin)
