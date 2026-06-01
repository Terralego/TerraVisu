import re
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from project.geosource.tests.factories import PostGISSourceFactory
from project.terra_layer.models import CustomStyle, FilterField, Layer
from project.terra_layer.tests.factories import (
    FieldFactory,
    LayerFactory,
    LayerGroupFactory,
)


class DuplicateLayerTestCase(TestCase):
    """
    Duplicate a "Communes 2019" layer to create a "Communes 2020" layer with a new source
    We have a layer called "Communes 2019" attached to source "communes_2019" (PostGIS). It has:
    - A main_field pointing to field "nom_2019" on the original source
    - A legend with title "Communes 2019" and comment "Données 2019"
    - A popup_config whose template references "nom_2019" and whose wizard contains a sourceFieldId pointing to the nom_2019 field
    - A minisheet_config whose template references "nom_2019" and whose wizard has a tree item and a title both referencing nom_2019 via sourceFieldId
    - A FilterField (fields_filters) linking the layer to field nom_2019
    - Two extra styles (CustomStyle): one attached to source "extra_2019" (to be replaced), one attached to source "extra_keep" (to be kept with "_")
    - The layer belongs to a group (scene)

    We want to duplicate it onto a new source "communes_2020" which has a field "nom_2020" instead of "nom_2019", update all text references, and keep it in the same scene.
    """

    @classmethod
    def setUpTestData(cls):
        # Original source + fields
        cls.source_2019 = PostGISSourceFactory(name="communes_2019")
        cls.field_nom_2019 = FieldFactory(
            source=cls.source_2019, name="nom_2019", label="Nom 2019"
        )
        cls.field_pop_2019 = FieldFactory(
            source=cls.source_2019, name="pop_2019", label="Population 2019"
        )

        # Target source + fields
        cls.source_2020 = PostGISSourceFactory(name="communes_2020")
        cls.field_nom_2020 = FieldFactory(
            source=cls.source_2020, name="nom_2020", label="Nom 2020"
        )
        cls.field_pop_2020 = FieldFactory(
            source=cls.source_2020, name="pop_2020", label="Population 2020"
        )

        # Extra style sources
        cls.extra_source_2019 = PostGISSourceFactory(name="extra_2019")
        cls.extra_source_2020 = PostGISSourceFactory(name="extra_2020")
        cls.extra_source_keep = PostGISSourceFactory(name="extra_keep")

        # Scene / group
        cls.group = LayerGroupFactory()

        # Layer
        cls.layer = LayerFactory(
            name="Communes 2019",
            source=cls.source_2019,
            main_field=cls.field_nom_2019,
            group=cls.group,
            legends=[
                {
                    "title": "Communes 2019",
                    "comment": "Données 2019",
                    "items": [],
                }
            ],
            popup_config={
                "template": "<h1>{{nom_2019}}</h1>",
                "wizard": {
                    "fields": [
                        {
                            "sourceFieldId": cls.field_nom_2019.pk,
                            "label": "Nom",
                        },
                    ]
                },
            },
            minisheet_config={
                "template": "<p>{{nom_2019}}</p>",
                "wizard": {
                    "title": {
                        "sourceFieldId": cls.field_nom_2019.pk,
                        "default": "Nom",
                    },
                    "tree": [
                        {
                            "sourceFieldId": cls.field_nom_2019.pk,
                            "label": "Nom",
                        },
                    ],
                },
            },
        )

        # FilterField
        FilterField.objects.create(
            layer=cls.layer,
            field=cls.field_nom_2019,
            label="Nom",
            filter_enable=True,
            exportable=True,
            shown=True,
        )

        # Extra styles (two: one to replace, one to keep)
        CustomStyle.objects.create(
            layer=cls.layer,
            source=cls.extra_source_2019,
            style_config={"type": "fill", "paint": {}},
        )
        CustomStyle.objects.create(
            layer=cls.layer,
            source=cls.extra_source_keep,
            style_config={"type": "line", "paint": {}},
        )

    def test_full_duplication_with_source_change(self):
        out = StringIO()
        call_command(
            "duplicate_layer",
            str(self.layer.pk),
            name="Communes 2020",
            source=self.source_2020.pk,
            main_field="nom_2020",
            preserve_scene=True,
            fields_mapping=["nom_2019,nom_2020", "pop_2019,pop_2020"],
            legend_titles_search_and_replace=["Communes 2019,Communes 2020"],
            legend_comments_search_and_replace=["Données 2019,Données 2020"],
            popup_search_and_replace=["nom_2019,nom_2020"],
            minisheet_search_and_replace=["nom_2019,nom_2020"],
            extra_styles_sources=f"{self.extra_source_2020.pk},_",
            verbosity=2,
            stdout=out,
        )

        clone_pk = int(re.findall(r"pk=(\d+)", out.getvalue())[0])
        clone = Layer.objects.get(pk=clone_pk)

        # Basic attributes
        self.assertEqual(clone.name, "Communes 2020")
        self.assertEqual(clone.source.pk, self.source_2020.pk)
        self.assertEqual(clone.main_field, self.field_nom_2020)
        self.assertEqual(clone.group, self.group)

        # Legends
        self.assertEqual(clone.legends[0]["title"], "Communes 2020")
        self.assertEqual(clone.legends[0]["comment"], "Données 2020")

        # Popup config: template text + wizard field ID remapped
        self.assertIn("nom_2020", clone.popup_config["template"])
        self.assertNotIn("nom_2019", clone.popup_config["template"])
        self.assertEqual(
            clone.popup_config["wizard"]["fields"][0]["sourceFieldId"],
            self.field_nom_2020.pk,
        )

        # Minisheet config: template text + wizard tree/title field IDs remapped
        self.assertIn("nom_2020", clone.minisheet_config["template"])
        self.assertNotIn("nom_2019", clone.minisheet_config["template"])
        self.assertEqual(
            clone.minisheet_config["wizard"]["tree"][0]["sourceFieldId"],
            self.field_nom_2020.pk,
        )
        self.assertEqual(
            clone.minisheet_config["wizard"]["title"]["sourceFieldId"],
            self.field_nom_2020.pk,
        )

        # FilterField cloned and remapped
        clone_filter = clone.fields_filters.first()
        self.assertEqual(clone_filter.field, self.field_nom_2020)
        self.assertEqual(clone_filter.field.source.pk, self.source_2020.pk)
        self.assertEqual(clone_filter.label, "Nom")
        self.assertTrue(clone_filter.filter_enable)
        self.assertTrue(clone_filter.exportable)
        self.assertTrue(clone_filter.shown)

        # Extra styles: first replaced, second kept ("_")
        clone_extras = list(clone.extra_styles.order_by("pk"))
        self.assertEqual(len(clone_extras), 2)
        self.assertEqual(clone_extras[0].source, self.extra_source_2020)
        self.assertEqual(clone_extras[1].source, self.extra_source_keep)

        # Success message
        self.assertIn("duplicated successfully", out.getvalue())


class DuplicateLayerSimpleTestCase(TestCase):
    """Test duplicating a layer without changing the source."""

    @classmethod
    def setUpTestData(cls):
        cls.source = PostGISSourceFactory(name="simple_source")
        cls.field = FieldFactory(source=cls.source, name="nom", label="Nom")
        cls.layer = LayerFactory(
            name="Simple Layer",
            source=cls.source,
            main_field=cls.field,
        )

    def test_simple_duplication_default_name(self):
        out = StringIO()
        call_command("duplicate_layer", str(self.layer.pk), stdout=out)

        clone_pk = int(re.findall(r"pk=(\d+)", out.getvalue())[0])
        clone = Layer.objects.get(pk=clone_pk)
        self.assertIn("Simple Layer", clone.name)
        self.assertIn("Copy", clone.name)
        self.assertEqual(clone.source.pk, self.source.pk)
        self.assertIsNone(clone.group)

    def test_simple_duplication_custom_name(self):
        out = StringIO()
        call_command(
            "duplicate_layer",
            str(self.layer.pk),
            name="My Custom Name",
            stdout=out,
        )
        clone_pk = int(re.findall(r"pk=(\d+)", out.getvalue())[0])
        clone = Layer.objects.get(pk=clone_pk)
        self.assertEqual(clone.name, "My Custom Name")


class DuplicateLayerErrorTestCase(TestCase):
    """Test error handling in the duplicate_layer command."""

    @classmethod
    def setUpTestData(cls):
        cls.source = PostGISSourceFactory(name="error_source")
        cls.field = FieldFactory(source=cls.source, name="nom", label="Nom")
        cls.layer = LayerFactory(
            name="Error Layer",
            source=cls.source,
            main_field=cls.field,
        )

    def test_nonexistent_layer(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("duplicate_layer", "999999", stdout=StringIO())
        self.assertIn("999999", str(ctx.exception))

    def test_source_without_main_field(self):
        other_source = PostGISSourceFactory(name="other_source")
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                source=other_source.pk,
                stdout=StringIO(),
            )
        self.assertIn("--main-field", str(ctx.exception))

    def test_nonexistent_source(self):
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                source=999999,
                main_field="nom",
                stdout=StringIO(),
            )
        self.assertIn("999999", str(ctx.exception))

    def test_nonexistent_main_field(self):
        other_source = PostGISSourceFactory(name="other_source_2")
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                source=other_source.pk,
                main_field="nonexistent_field",
                stdout=StringIO(),
            )
        self.assertIn("nonexistent_field", str(ctx.exception))

    def test_legend_title_not_found(self):
        self.layer.legends = [{"title": "Real Title", "comment": ""}]
        self.layer.save()
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                legend_titles_search_and_replace=["Wrong Title,New Title"],
                stdout=StringIO(),
            )
        self.assertIn("Wrong Title", str(ctx.exception))

    def test_extra_styles_count_mismatch(self):
        CustomStyle.objects.create(
            layer=self.layer,
            source=self.source,
            style_config={},
        )
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                extra_styles_sources="1,2",
                stdout=StringIO(),
            )
        self.assertIn("1 extra style", str(ctx.exception))

    def test_invalid_parse_pair_value(self):
        """parse_pair raises CommandError when value has no comma separator."""
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                legend_titles_search_and_replace=["no_comma_here"],
                stdout=StringIO(),
            )
        self.assertIn("Invalid", str(ctx.exception))
        self.assertIn("no_comma_here", str(ctx.exception))

    def test_field_not_on_original_source(self):
        """fields-mapping references a field name that doesn't exist on the original source."""
        target_source = PostGISSourceFactory(name="target_fm_orig")
        FieldFactory(source=target_source, name="nom_target", label="Nom Target")
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                source=target_source.pk,
                main_field="nom_target",
                fields_mapping=["nonexistent_old,nom_target"],
                stdout=StringIO(),
            )
        self.assertIn("nonexistent_old", str(ctx.exception))
        self.assertIn("original source", str(ctx.exception))

    def test_field_not_on_target_source(self):
        """fields-mapping references a new field name that doesn't exist on the target source."""
        target_source = PostGISSourceFactory(name="target_fm_target")
        FieldFactory(source=target_source, name="nom_target", label="Nom Target")
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                source=target_source.pk,
                main_field="nom_target",
                fields_mapping=["nom,nonexistent_new"],
                stdout=StringIO(),
            )
        self.assertIn("nonexistent_new", str(ctx.exception))
        self.assertIn("target source", str(ctx.exception))

    def test_fields_mapping_missing_required_field(self):
        """When source changes and a field filter references a field not in the mapping."""
        target_source = PostGISSourceFactory(name="target_fm_missing")
        FieldFactory(source=target_source, name="nom_target", label="Nom Target")
        # Add a filter field on the layer so clone_fields_filters needs a mapping
        FilterField.objects.create(
            layer=self.layer,
            field=self.field,
            label="Nom Filter",
            filter_enable=True,
            exportable=True,
            shown=True,
        )
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                source=target_source.pk,
                main_field="nom_target",
                # No fields_mapping provided, so "nom" won't be found on target
                stdout=StringIO(),
            )
        self.assertIn("nom", str(ctx.exception))
        self.assertIn("Fields mapping need to include", str(ctx.exception))

    def test_popup_search_string_not_found(self):
        """popup-search-and-replace raises when the old string isn't in popup config."""
        self.layer.popup_config = {
            "template": "<h1>Hello</h1>",
            "wizard": {"fields": []},
        }
        self.layer.save()
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                popup_search_and_replace=["not_in_popup,replacement"],
                stdout=StringIO(),
            )
        self.assertIn("not_in_popup", str(ctx.exception))
        self.assertIn("popup config", str(ctx.exception))

    def test_minisheet_search_string_not_found(self):
        """minisheet-search-and-replace raises when the old string isn't in minisheet config."""
        self.layer.minisheet_config = {
            "template": "<p>Hello</p>",
            "wizard": {"tree": [], "title": {}},
        }
        self.layer.save()
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                minisheet_search_and_replace=["not_in_minisheet,replacement"],
                stdout=StringIO(),
            )
        self.assertIn("not_in_minisheet", str(ctx.exception))
        self.assertIn("minisheet config", str(ctx.exception))

    def test_extra_styles_sources_invalid_value(self):
        """Non-integer, non-underscore value in --extra-styles-sources raises."""
        CustomStyle.objects.create(
            layer=self.layer,
            source=self.source,
            style_config={},
        )
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                extra_styles_sources="abc",
                stdout=StringIO(),
            )
        self.assertIn("abc", str(ctx.exception))
        self.assertIn("Invalid value", str(ctx.exception))

    def test_legend_comment_not_found(self):
        """legend-comments-search-and-replace raises when comment isn't found."""
        self.layer.legends = [{"title": "Title", "comment": "Real comment"}]
        self.layer.save()
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                legend_comments_search_and_replace=["Wrong comment,New comment"],
                stdout=StringIO(),
            )
        self.assertIn("Wrong comment", str(ctx.exception))

    def test_fields_mapping_stores_mapping(self):
        """Valid fields-mapping populates fields_mapping dict and remaps fields correctly."""
        target_source = PostGISSourceFactory(name="target_fm_ok")
        target_field = FieldFactory(
            source=target_source, name="nom_target", label="Nom Target"
        )
        automatic_original_field = FieldFactory(
            source=self.source, name="nom_champs_2", label="Nom Champs 2"
        )
        automatic_target_field = FieldFactory(
            source=target_source, name="nom_champs_2", label="Nom Champs 2"
        )
        FilterField.objects.create(
            layer=self.layer,
            field=automatic_original_field,
            label="Nom Champs 2 FilterField",
            filter_enable=True,
            exportable=True,
            shown=True,
        )
        FilterField.objects.create(
            layer=self.layer,
            field=self.field,
            label="Nom Filter",
            filter_enable=True,
            exportable=True,
            shown=True,
        )
        out = StringIO()
        call_command(
            "duplicate_layer",
            str(self.layer.pk),
            source=target_source.pk,
            main_field="nom_target",
            fields_mapping=["nom,nom_target"],
            stdout=out,
        )
        clone_pk = int(re.findall(r"pk=(\d+)", out.getvalue())[0])
        clone = Layer.objects.get(pk=clone_pk)
        # FilterField should be remapped to the target field
        self.assertEqual(clone.fields_filters.count(), 2)
        self.assertIn(
            automatic_target_field.pk,
            clone.fields_filters.all().values_list("field", flat=True),
        )
        self.assertIn(
            target_field.pk, clone.fields_filters.all().values_list("field", flat=True)
        )

    def test_extra_styles_sources_nonexistent_source(self):
        """Valid integer PK that doesn't match any source raises."""
        CustomStyle.objects.create(
            layer=self.layer,
            source=self.source,
            style_config={},
        )
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "duplicate_layer",
                str(self.layer.pk),
                extra_styles_sources="999999",
                stdout=StringIO(),
            )
        self.assertIn("999999", str(ctx.exception))
        self.assertIn("does not exist", str(ctx.exception))
