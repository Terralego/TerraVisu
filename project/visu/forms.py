from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, ModelForm
from django.utils.translation import gettext_lazy as _

from project.visu.models import (
    SheetBlock,
    SheetBlockType,
    SheetFieldType,
)


class SheetFieldInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        block_type = self.instance.type
        fields_source = self.instance.fields_source

        fields = [
            form.cleaned_data["field"]
            for form in self.forms
            if form.cleaned_data
            and not form.cleaned_data.get("DELETE")
            and form.cleaned_data.get("field")
        ]

        if not fields:
            return

        if block_type in [
            SheetBlockType.RADAR_PLOT,
            SheetBlockType.BAR_PLOT,
            SheetBlockType.DISTRIB_PLOT,
            SheetBlockType.BOOLEANS,
        ]:
            expected_type = (
                SheetFieldType.NUMERICAL
                if block_type != SheetBlockType.BOOLEANS
                else SheetFieldType.BOOLEAN
            )
            type_label = (
                _("NUMERICAL")
                if block_type != SheetBlockType.BOOLEANS
                else _("BOOLEAN")
            )
            wrong_type_fields = [f for f in fields if f.type != expected_type]
            if wrong_type_fields:
                field_names = ", ".join([f.label for f in wrong_type_fields])
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

        wrong_source_fields = [f for f in fields if f.field.source != fields_source]
        if wrong_source_fields:
            field_names = ", ".join([f.label for f in wrong_source_fields])
            raise ValidationError(
                _(
                    "The following fields do not belong to the selected source: %(field_names)s"
                )
                % {"field_names": field_names}
            )


class ExtraSheetFieldInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        fields_source = self.instance.fields_source

        extra_fields = [
            form.cleaned_data["extra_field"]
            for form in self.forms
            if form.cleaned_data
            and not form.cleaned_data.get("DELETE")
            and form.cleaned_data.get("extra_field")
        ]

        if not extra_fields:
            return

        wrong_source_fields = [
            f for f in extra_fields if f.field.source != fields_source
        ]
        if wrong_source_fields:
            field_names = ", ".join([f.label for f in wrong_source_fields])
            raise ValidationError(
                _(
                    "The following extra fields do not belong to the selected source: %(field_names)s"
                )
                % {"field_names": field_names}
            )


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
        # fields = cleaned_data.get("fields", [])
        order_field = cleaned_data.get("order_field", [])
        # extra_fields = cleaned_data.get("extra_fields", [])
        # all_fields =   extra_fields
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
