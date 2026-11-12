import json
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import gettext as _

from project.geosource.models import Field, Source
from project.terra_layer.models import FilterField, Layer


class Command(BaseCommand):
    help = "Duplicate a layer by its primary key and optionally update the duplicate"
    fields_mapping = {}

    def parse_pair(self, value, option_name):
        """Split on the first unescaped comma, unescape \\, and validate exactly two parts."""
        parts = re.split(r"(?<!\\),", value, maxsplit=1)
        if len(parts) != 2:
            raise CommandError(
                _(
                    "Invalid %(option)s value '%(value)s'. "
                    'Expected format: "old_value,new_value"'
                )
                % {"option": option_name, "value": value}
            )
        return [p.replace("\\,", ",") for p in parts]

    def prepare_fields_mapping(self, layer, target_source, fields_mapping_options):
        if fields_mapping_options:
            for pair in fields_mapping_options:
                old_name, new_name = self.parse_pair(pair, "fields-mapping")
                try:
                    old_field = Field.objects.get(source=layer.source, name=old_name)
                except Field.DoesNotExist:
                    raise CommandError(
                        _(
                            "Field '%(name)s' does not exist on original source %(source)s"
                        )
                        % {"name": old_name, "source": layer.source.pk}
                    )
                try:
                    new_field = Field.objects.get(source=target_source, name=new_name)
                    self.fields_mapping[old_field.pk] = new_field.pk
                except Field.DoesNotExist:
                    raise CommandError(
                        _("Field '%(name)s' does not exist on target source %(source)s")
                        % {"name": new_name, "source": target_source.pk}
                    )

    def get_target_field(self, old_field, target_source):
        if old_field.pk not in self.fields_mapping:
            try:
                new_field = Field.objects.get(source=target_source, name=old_field.name)
                self.fields_mapping[old_field.pk] = new_field.pk
                return new_field
            except Field.DoesNotExist:
                raise CommandError(
                    _("Fields mapping need to include '%(old_field_name)s'.")
                    % {"old_field_name": old_field.name}
                )
        return Field.objects.get(pk=self.fields_mapping[old_field.pk])

    def clone_fields_filters(self, original_layer, cloned_layer):
        for field_filter in original_layer.fields_filters.all():
            old_field = field_filter.field
            new_field = self.get_target_field(old_field, cloned_layer.source)
            attrs = {
                "layer": cloned_layer,
                "field": new_field,
            }
            field_filter.make_clone(attrs)

    def add_arguments(self, parser):
        parser.add_argument(
            "pk",
            type=int,
            help=_("Primary key of the layer to duplicate"),
        )
        parser.add_argument(
            "--name",
            type=str,
            default=None,
            help=_("Custom name for the duplicated layer"),
        )
        parser.add_argument(
            "--source",
            type=int,
            default=None,
            help=_("Primary key of the source to use for the duplicated layer"),
        )
        parser.add_argument(
            "--main-field",
            type=str,
            default=None,
            help=_(
                "Name of the field to use as main_field for the duplicated layer. "
                "The field is looked up on the target source. "
                "Mandatory when --source is specified."
            ),
        )
        parser.add_argument(
            "--extra-styles-sources",
            type=str,
            default=None,
            help=_(
                "Source PKs for extra styles, comma-separated in order. "
                'Use "_" to keep the original source. '
                'Example: "12,_,17" updates 1st and 3rd extra style sources.'
            ),
        )
        parser.add_argument(
            "--legend-titles-search-and-replace",
            nargs="*",
            default=None,
            help=_(
                'Rename legend titles. Each value is "old_title,new_title". '
                'Example: --legend-titles-search-and-replace "Old title,New title" "Other title,Changed title"'
            ),
        )
        parser.add_argument(
            "--legend-comments-search-and-replace",
            nargs="*",
            default=None,
            help=_(
                'Update legend comments. Each value is "old_comment,new_comment". '
                'Example: --legend-comments-search-and-replace "Old comment,New comment here"'
            ),
        )
        parser.add_argument(
            "--popup-search-and-replace",
            nargs="*",
            default=None,
            help=_(
                'Search and replace in popup template. Each value is "old_string,new_string". '
                'Example: --popup-search-and-replace "old text,new text"'
            ),
        )
        parser.add_argument(
            "--minisheet-search-and-replace",
            nargs="*",
            default=None,
            help=_(
                'Search and replace in minisheet template. Each value is "old_string,new_string". '
                'Example: --minisheet-search-and-replace "old text,new text"'
            ),
        )
        parser.add_argument(
            "--preserve-scene",
            action="store_true",
            default=False,
            help=_(
                "Keep the duplicated layer in the same scene (group) as the original. "
                "By default the clone is detached from any scene."
            ),
        )
        parser.add_argument(
            "--fields-mapping",
            nargs="*",
            default=None,
            help=_(
                "Map fields from the original source to the target source. "
                'Each value is "old_field_name,new_field_name". '
                'Example: --fields-mapping "nom_m,name_field" "pop,population".'
            ),
        )
        parser.add_argument(
            "--table",
            nargs="*",
            default=None,
            help=_(
                "List fields to configure for the Table. Each field will be exportable and displayed in table by default."
                'Each value is "field_name,field_label". '
                'Example: --table "nom_m,Nom" "pop,Population".'
            ),
        )
        parser.add_argument(
            "--filter-settings",
            nargs="*",
            default=None,
            help=_(
                "Configure filter settings for fields. Each value is 'field_name:JSON_CONFIG'. "
                'Example: --filter-settings \'nom_region:{"type":"range","proposeValues":"all","fetchValue":true}\' '
                '\'nom_dep:{"type":"range","values":[1,12,66],"fetchValue":false,"proposeValues":"custom","range_format":"number"}\'. '
                'Possible type values: "single", "many", "range". '
                'Possible proposeValues values: "none", "all", "list", "custom". '
                'Possible range_format values: "number", "date". '
                'range_format is only required when proposeValues is "custom".'
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Get layer to duplicate
        try:
            layer = Layer.objects.get(pk=options["pk"])
        except Layer.DoesNotExist:
            raise CommandError(
                _("Layer with pk %(pk)s does not exist") % {"pk": options["pk"]}
            )

        # Build duplication parameters, and prepare fields mapping if source will be changed
        attrs = {}
        if options["name"]:
            attrs["name"] = options["name"]
        else:
            attrs["name"] = f"{layer.name} (" + str(_("Copy")) + ")"

        if options["preserve_scene"]:
            attrs["group"] = layer.group

        source_changed = False
        if options["source"]:
            if not options["main_field"]:
                raise CommandError(
                    _("--main-field is required when --source is specified")
                )
            try:
                target_source = Source.objects.get(pk=options["source"])
                attrs["source"] = target_source
                attrs["main_field"] = Field.objects.get(
                    source=target_source, name=options["main_field"]
                )
                source_changed = True
            except Source.DoesNotExist:
                raise CommandError(
                    _("Source with pk %(pk)s does not exist")
                    % {"pk": options["source"]}
                )
            except Field.DoesNotExist:
                raise CommandError(
                    _("Field '%(name)s' does not exist on source %(source)s")
                    % {"name": options["main_field"], "source": target_source.pk}
                )
            self.prepare_fields_mapping(
                layer, target_source, options.get("fields_mapping", [])
            )

        # Clone layer using attributes
        # Make sure to handle fields filters manually if source changed
        clone = layer.make_clone(attrs=attrs, skip_fields_filters=source_changed)
        if source_changed:
            self.clone_fields_filters(layer, clone)

        # Update the clone's legend
        clone_modified = False
        if options["legend_titles_search_and_replace"]:
            for pair in options["legend_titles_search_and_replace"]:
                old_title, new_title = self.parse_pair(
                    pair, "legend-titles-search-and-replace"
                )
                found = False
                for legend in clone.legends:
                    title_before = legend.get("title", "")
                    title_after = title_before.replace(old_title, new_title)
                    if title_before != title_after:
                        legend["title"] = title_after
                        found = True
                if not found:
                    raise CommandError(
                        _("No legend with title '%(title)s' found")
                        % {"title": old_title}
                    )
            clone_modified = True
        if options["legend_comments_search_and_replace"]:
            for pair in options["legend_comments_search_and_replace"]:
                old_comment, new_comment = self.parse_pair(
                    pair, "legend-comments-search-and-replace"
                )
                found = False
                for legend in clone.legends:
                    comment_before = legend.get("comment", "")
                    comment_after = comment_before.replace(old_comment, new_comment)
                    if comment_before != comment_after:
                        legend["comment"] = comment_after
                        found = True
                if not found:
                    raise CommandError(
                        _("No legend with comment '%(comment)s' found")
                        % {"comment": old_comment}
                    )
            clone_modified = True

        # Update the clone's popup
        if options["popup_search_and_replace"]:
            popup_text = json.dumps(clone.popup_config, ensure_ascii=False)
            for pair in options["popup_search_and_replace"]:
                old_string, new_string = self.parse_pair(
                    pair, "popup-search-and-replace"
                )
                if old_string not in popup_text:
                    raise CommandError(
                        _("String '%(string)s' not found in popup config")
                        % {"string": old_string}
                    )
                popup_text = popup_text.replace(old_string, new_string)
            clone.popup_config = json.loads(popup_text)
            clone_modified = True
            if options["verbosity"] >= 2:
                self.stdout.write(
                    _("Popup template:")
                    + f"\n{clone.popup_config.get('template', '')}\n\n"
                )

        # Update the clone's minisheet
        if options["minisheet_search_and_replace"]:
            minisheet_text = json.dumps(clone.minisheet_config, ensure_ascii=False)
            for pair in options["minisheet_search_and_replace"]:
                old_string, new_string = self.parse_pair(
                    pair, "minisheet-search-and-replace"
                )
                if old_string not in minisheet_text:
                    raise CommandError(
                        _("String '%(string)s' not found in minisheet config")
                        % {"string": old_string}
                    )
                minisheet_text = minisheet_text.replace(old_string, new_string)
            clone.minisheet_config = json.loads(minisheet_text)
            clone_modified = True
            if options["verbosity"] >= 2:
                self.stdout.write(
                    _("Minisheet template:")
                    + f"\n{clone.minisheet_config.get('template', '')}\n\n"
                )

        # Update the clone's fields using fields mapping if source was changed
        if options["source"]:
            # Handle fields in minisheet config if source was changed
            if "tree" in clone.minisheet_config.get("wizard", {}):
                for item in clone.minisheet_config["wizard"]["tree"]:
                    if "sourceFieldId" in item:
                        old_field_id = item["sourceFieldId"]
                        new_field_id = self.fields_mapping[old_field_id]
                        item["sourceFieldId"] = new_field_id
                        clone_modified = True
                        if options["verbosity"] >= 2:
                            self.stdout.write(
                                _("Minisheet config:")
                                + f"\n{clone.minisheet_config}\n\n"
                            )
                if "title" in clone.minisheet_config["wizard"]:
                    old_field_id = clone.minisheet_config["wizard"]["title"][
                        "sourceFieldId"
                    ]
                    new_field_id = self.fields_mapping[old_field_id]
                    clone.minisheet_config["wizard"]["title"]["sourceFieldId"] = (
                        new_field_id
                    )
                    clone_modified = True
            # Handle fields in popup config if source was changed
            if "fields" in clone.popup_config.get("wizard", {}):
                for item in clone.popup_config["wizard"]["fields"]:
                    if "sourceFieldId" in item:
                        old_field_id = item["sourceFieldId"]
                        new_field_id = self.fields_mapping[old_field_id]
                        item["sourceFieldId"] = new_field_id
                        clone_modified = True
                        if options["verbosity"] >= 2:
                            self.stdout.write(
                                _("Popup config:") + f"\n{clone.popup_config}\n\n"
                            )

        # Update the clone's extra styles sources
        if options["extra_styles_sources"]:
            extra_sources_map = {}
            extra_styles_count = layer.extra_styles.count()
            source_values = options["extra_styles_sources"].split(",")
            if len(source_values) != extra_styles_count:
                raise CommandError(
                    _(
                        "This layer has %(expected)s extra style(s), please enter as many sources (found %(got)s sources)"
                    )
                    % {
                        "expected": extra_styles_count,
                        "got": len(source_values),
                    }
                )
            for i, value in enumerate(source_values):
                value = value.strip()
                if value == "_":
                    continue
                try:
                    source_pk = int(value)
                except ValueError:
                    raise CommandError(
                        _(
                            "Invalid value '%(value)s' in --extra-styles-sources. "
                            'Expected an integer PK or "_".'
                        )
                        % {"value": value}
                    )
                try:
                    extra_sources_map[i] = Source.objects.get(pk=source_pk)
                    cloned_extra_styles = list(clone.extra_styles.order_by("pk"))
                    for idx, source in extra_sources_map.items():
                        cloned_extra_styles[idx].source = source
                        cloned_extra_styles[idx].save(update_fields=["source"])
                except Source.DoesNotExist:
                    raise CommandError(
                        _("Source with pk %(pk)s does not exist") % {"pk": source_pk}
                    )

        # Update the table configuration
        if options["table"]:
            for pair in options.get("table", []):
                name, label = self.parse_pair(pair, "table")
                field = Field.objects.get(source=clone.source, name=name)
                defaults = {
                    "label": label,
                    "shown": True,
                    "display": True,
                    "exportable": True,
                }
                filter_field, created = FilterField.objects.update_or_create(
                    field=field,
                    layer=clone,
                    defaults=defaults,
                    create_defaults=defaults,
                )
                if options["verbosity"] >= 2:
                    if created:
                        self.stdout.write(
                            f"Created FilterField {filter_field.pk} for {name} - {label}"
                        )
                    else:
                        self.stdout.write(
                            f"Updated FilterField {filter_field.pk} for {name} - {label}"
                        )

        # param --filter-settings '' should only empty filters
        empty_filters = options.get("filter_settings") == [""]
        new_filters = options.get("filter_settings") and not empty_filters
        if empty_filters or new_filters:
            # First empty filters that were copied
            filter_fields = list(FilterField.objects.filter(layer=clone))
            for ff in filter_fields:
                ff.filter_enable = False
                ff.filter_settings = {}
            if filter_fields:
                FilterField.objects.bulk_update(
                    filter_fields, ["filter_enable", "filter_settings"]
                )

        filter_settings_data = {}
        if new_filters:
            for item in options.get("filter_settings"):
                field_name, config_str = item.split(":", 1)
                field_name = field_name.strip()
                config_str = config_str.strip()
                config_dict = json.loads(config_str.strip())
                filter_settings_data[field_name] = config_dict

            for order, (field_name, config) in enumerate(filter_settings_data.items()):
                try:
                    field = Field.objects.get(source=clone.source, name=field_name)
                except Field.DoesNotExist:
                    raise CommandError(
                        _("Field '%(name)s' does not exist on source %(source)s")
                        % {"name": field_name, "source": clone.source.pk}
                    )

                try:
                    filter_field = FilterField.objects.get(field=field, layer=clone)
                except FilterField.DoesNotExist:
                    raise CommandError(
                        _(
                            "No FilterField found for field '%(name)s' on layer %(layer)s"
                        )
                        % {"name": field_name, "layer": clone.pk}
                    )

                filter_field.order = order
                filter_field.filter_enable = True
                filter_field.filter_settings = {
                    "type": config.get("type"),
                    "values": config.get("values", []),
                    "proposeValues": config.get("proposeValues"),
                }
                if config.get("range_format"):
                    filter_field.filter_settings["range_format"] = config[
                        "range_format"
                    ]
                if config.get("fetchValue") is not None:
                    filter_field.filter_settings["fetchValue"] = config["fetchValue"]

                filter_field.format_type = (
                    config.get("range_format", "")
                    if config.get("proposeValues") == "custom"
                    else ""
                )
                filter_field.save()

                if options["verbosity"] >= 2:
                    self.stdout.write(
                        f"Updated FilterField {filter_field.pk} for {field_name} with filter settings {filter_field.filter_settings}"
                    )

        # Save the clone's updates
        if clone_modified:
            clone.save(wizard_update=True)

        self.stdout.write(
            _(
                "Layer %(old_pk)s duplicated successfully. "
                'New layer: pk=%(new_pk)s, name="%(name)s"'
            )
            % {"old_pk": layer.pk, "new_pk": clone.pk, "name": clone.name}
        )
