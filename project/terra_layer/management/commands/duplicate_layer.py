import json
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import gettext as _

from project.geosource.models import Field, Source
from project.terra_layer.models import Layer


def parse_pair(value, option_name):
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


class Command(BaseCommand):
    help = "Duplicate a layer by its primary key and optionally update the duplicate"
    fields_mapping = {}

    def prepare_fields_mapping(self, layer, target_source, fields_mapping_options):
        if fields_mapping_options:
            for pair in fields_mapping_options:
                old_name, new_name = parse_pair(pair, "fields-mapping")
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
        clone = layer.make_clone(attrs=attrs)
        self.clone_fields_filters(layer, clone)

        # Update the clone's legend
        clone_modified = False
        if options["legend_titles_search_and_replace"]:
            for pair in options["legend_titles_search_and_replace"]:
                old_title, new_title = parse_pair(
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
                old_comment, new_comment = parse_pair(
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
                old_string, new_string = parse_pair(pair, "popup-search-and-replace")
                if old_string not in popup_text:
                    raise CommandError(
                        _("String '%(string)s' not found in popup config")
                        % {"string": old_string}
                    )
                popup_text = popup_text.replace(old_string, new_string)
            clone.popup_config = json.loads(popup_text)
            clone_modified = True
            if options["verbosity"] >= 1:
                self.stdout.write(
                    _("Popup template:")
                    + f"\n{clone.popup_config.get('template', '')}\n\n"
                )

        # Update the clone's minisheet
        if options["minisheet_search_and_replace"]:
            minisheet_text = json.dumps(clone.minisheet_config, ensure_ascii=False)
            for pair in options["minisheet_search_and_replace"]:
                old_string, new_string = parse_pair(
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
            if options["verbosity"] >= 1:
                self.stdout.write(
                    _("Minisheet template:")
                    + f"\n{clone.minisheet_config.get('template', '')}\n\n"
                )

        # Update the clone's fields using fields mapping if source was changed
        if options["source"]:
            # Handle fields in minisheet config if source was changed
            if "tree" in clone.minisheet_config["wizard"]:
                for item in clone.minisheet_config["wizard"]["tree"]:
                    if "sourceFieldId" in item:
                        old_field_id = item["sourceFieldId"]
                        new_field_id = self.fields_mapping[old_field_id]
                        item["sourceFieldId"] = new_field_id
                        clone_modified = True
                        if options["verbosity"] >= 1:
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
            for item in clone.popup_config["wizard"]["fields"]:
                if "sourceFieldId" in item:
                    old_field_id = item["sourceFieldId"]
                    new_field_id = self.fields_mapping[old_field_id]
                    item["sourceFieldId"] = new_field_id
                    clone_modified = True
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
