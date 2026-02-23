from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, ModelForm
from django.utils.translation import gettext_lazy as _

from project.geosource.models import Field
from project.visu.models import (
    FeatureSheet,
    SheetBlock,
    SheetBlockType,
    SheetFieldType,
)


class BaseSheetFieldInlineFormSet(BaseInlineFormSet):
    field_key: str = None

    def get_fields(self):
        return [
            form.cleaned_data[self.field_key]
            for form in self.forms
            if form.cleaned_data
            and not form.cleaned_data.get("DELETE")
            and form.cleaned_data.get(self.field_key)
        ]

    def validate_sources(self, fields, fields_source):
        wrong_source_fields = [f for f in fields if f.field.source != fields_source]
        if wrong_source_fields:
            field_names = ", ".join(f.label for f in wrong_source_fields)
            raise ValidationError(
                _(
                    "The following fields do not belong to the selected source: %(field_names)s"
                )
                % {"field_names": field_names}
            )

    PLOT_BLOCK_TYPES = {
        SheetBlockType.RADAR_PLOT,
        SheetBlockType.BAR_PLOT,
        SheetBlockType.DISTRIB_PLOT,
        SheetBlockType.BOOLEANS,
    }
    EXPECTED_FIELD_TYPE = {
        SheetBlockType.BOOLEANS: (SheetFieldType.BOOLEAN, _("BOOLEAN")),
    }
    DEFAULT_FIELD_TYPE = (SheetFieldType.NUMERICAL, _("NUMERICAL"))

    def validate_field_types(self, fields, block_type):
        expected_type, type_label = self.EXPECTED_FIELD_TYPE.get(
            block_type, self.DEFAULT_FIELD_TYPE
        )
        wrong_type_fields = [f for f in fields if f.type != expected_type]
        if wrong_type_fields:
            field_names = ", ".join(f.label for f in wrong_type_fields)
            raise ValidationError(
                _(
                    "Block type '%(block_type)s' requires all fields to be %(type_label)s. "
                    "The following fields are not: %(field_names)s"
                )
                % {
                    "block_type": dict(SheetBlockType.choices)[block_type],
                    "type_label": type_label,
                    "field_names": field_names,
                }
            )

    def clean(self):
        super().clean()
        fields = self.get_fields()
        self.validate_sources(fields, self.instance.fields_source)
        block_type = self.instance.type
        if block_type in self.PLOT_BLOCK_TYPES:
            self.validate_field_types(fields, block_type)


class SheetFieldInlineFormSet(BaseSheetFieldInlineFormSet):
    field_key = "field"


class ExtraSheetFieldInlineFormSet(BaseSheetFieldInlineFormSet):
    field_key = "extra_field"


class SheetListFieldInlineFormSet(BaseInlineFormSet):
    def get_active_fields(self):
        return [
            form.cleaned_data["list_field"]
            for form in self.forms
            if form.cleaned_data
            and not form.cleaned_data.get("DELETE")
            and form.cleaned_data.get("list_field")
        ]

    def validate_same_source(self, fields):
        sources = []
        for f in fields:
            if f.source not in sources:
                sources.append(f.source)
        if len(sources) > 1:
            raise ValidationError(
                _("Sheets list fields must all come from the same source.")
            )

    def clean(self):
        super().clean()
        fields = self.get_active_fields()
        self.validate_same_source(fields)


class SheetBlockAdminForm(ModelForm):
    class Meta:
        model = SheetBlock
        fields = (
            "sheet",
            "title",
            "display_title",
            "type",
            "fields_source",
            "first_geom_source",
            "second_geom_source",
            "fields",
            "extra_fields",
            "order_field",
            "limit",
            "text",
            "fields_source",
            "first_geom_source",
            "second_geom_source",
        )

    def clean(self):
        cleaned_data = super().clean()
        block_type = cleaned_data.get("type")
        order_field = cleaned_data.get("order_field", [])
        first_geom_source = cleaned_data.get("first_geom_source")
        second_geom_source = cleaned_data.get("second_geom_source")
        fields_source = cleaned_data.get("fields_source")
        sheet = cleaned_data.get("sheet")

        # --- Mandatory source validation per block type ---
        # fields_source + fields:                          FIELDS, BOOLEANS, BAR_PLOT, DISTRIB_PLOT
        # fields_source + fields + extra_fields:           RADAR_PLOT
        # fields_source + fields + order + limit:          FIELDS_TABLE
        # first_geom_source:                               PANORAMAX
        # first_geom_source + second_geom_source (opt):    MAP

        REQUIRES_FIELDS_SOURCE = {
            SheetBlockType.FIELDS,
            SheetBlockType.BOOLEANS,
            SheetBlockType.BAR_PLOT,
            SheetBlockType.DISTRIB_PLOT,
            SheetBlockType.RADAR_PLOT,
            SheetBlockType.FIELDS_TABLE,
        }
        REQUIRES_FIRST_GEOM_SOURCE = {
            SheetBlockType.PANORAMAX,
            SheetBlockType.MAP,
        }

        if block_type in REQUIRES_FIELDS_SOURCE and not fields_source:
            raise ValidationError(
                _("Block type '%(block_type)s' requires a fields source.")
                % {"block_type": dict(SheetBlockType.choices)[block_type]}
            )

        if block_type in REQUIRES_FIRST_GEOM_SOURCE and not first_geom_source:
            raise ValidationError(
                _("Block type '%(block_type)s' requires a geometry source.")
                % {"block_type": dict(SheetBlockType.choices)[block_type]}
            )

        # --- Source validation from sheet ---

        sheet_sources = sheet.sources.all() if sheet else []
        sources_to_check = [
            s
            for s in [fields_source, first_geom_source, second_geom_source]
            if s is not None
        ]
        invalid_sources = [s for s in sources_to_check if s not in sheet_sources]
        if invalid_sources:
            raise ValidationError(
                _("Selected source does not match the sources of the Feature Sheet")
            )
        if order_field and order_field.source != fields_source:
            raise ValidationError(
                _("Order field must be from selected source '%(fields_source)s'.")
                % {"fields_source": fields_source}
            )
        return cleaned_data


class FeatureSheetAdminForm(ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        sources = cleaned_data.get("sources")
        unique_identifier = cleaned_data.get("unique_identifier")
        for source in sources:
            if (
                unique_identifier.source != source
                and not Field.objects.filter(
                    name=unique_identifier.name, source=source
                ).exists()
            ):
                raise ValidationError(
                    _(
                        "Field '%(unique_identifier)s' does not exist in source '%(source)s'."
                    )
                    % {
                        "unique_identifier": unique_identifier.name,
                        "source": source.name,
                    }
                )
        return cleaned_data

    class Meta:
        model = FeatureSheet
        fields = (
            "name",
            "unique_identifier",
            "sources",
        )
