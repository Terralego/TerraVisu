from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from ...geosource.models import FieldTypes
from ...geosource.tests.factories import PostGISSourceFactory
from ..models import (
    CustomStyle,
    Extent,
    ExtentCategory,
    FilterField,
    Layer,
    ReportField,
    Scene,
    SceneExtent,
    StyleImage,
)
from .factories import (
    LayerFactory,
    LayerGroupFactory,
    ReportFactory,
    SceneFactory,
    StyleImageFactory,
)


class LayerTestCase(TestCase):
    def test_str(self):
        layer = LayerFactory(
            name="foo",
            uuid="91c60192-9060-4bf6-b0de-818c5a362d89",
        )
        layer = Layer.objects.get(id=layer.id)
        self.assertEqual(
            str(layer),
            f"Layer ({layer.id}) - {layer.name} - ({layer.layer_identifier})",
        )

    def test_scene_insert_in_tree(self):
        scene = SceneFactory()
        source = PostGISSourceFactory()

        # Initial value
        self.assertEqual(scene.tree, [])

        layer = LayerFactory(source=source, name="")
        layer2 = LayerFactory(source=source, name="")
        layer3 = LayerFactory(source=source, name="")
        layer4 = LayerFactory(source=source, name="")

        scene.insert_in_tree(layer, ["level1", "level2"])

        # After first insertion
        self.assertEqual(
            scene.tree,
            [
                {
                    "group": True,
                    "label": "level1",
                    "children": [
                        {
                            "group": True,
                            "label": "level2",
                            "children": [{"geolayer": layer.id}],
                        }
                    ],
                }
            ],
        )

        scene.insert_in_tree(layer2, ["level1"])

        # After second insertion
        self.assertEqual(
            scene.tree,
            [
                {
                    "group": True,
                    "label": "level1",
                    "children": [
                        {
                            "group": True,
                            "label": "level2",
                            "children": [{"geolayer": layer.id}],
                        },
                        {"geolayer": layer2.id},
                    ],
                }
            ],
        )

        scene.insert_in_tree(layer3, ["level1Foo"])

        # After third insertion
        self.assertEqual(
            scene.tree,
            [
                {
                    "group": True,
                    "label": "level1",
                    "children": [
                        {
                            "group": True,
                            "label": "level2",
                            "children": [{"geolayer": layer.id}],
                        },
                        {"geolayer": layer2.id},
                    ],
                },
                {
                    "group": True,
                    "label": "level1Foo",
                    "children": [{"geolayer": layer3.id}],
                },
            ],
        )

        scene.insert_in_tree(
            layer4, ["level1Foo", "level2"], group_config={"selectors": []}
        )

        # After third insertion
        self.assertEqual(
            scene.tree,
            [
                {
                    "group": True,
                    "label": "level1",
                    "children": [
                        {
                            "group": True,
                            "label": "level2",
                            "children": [{"geolayer": layer.id}],
                        },
                        {"geolayer": layer2.id},
                    ],
                },
                {
                    "group": True,
                    "label": "level1Foo",
                    "children": [
                        {"geolayer": layer3.id},
                        {
                            "group": True,
                            "label": "level2",
                            "children": [{"geolayer": layer4.id}],
                            "selectors": [],
                        },
                    ],
                },
            ],
        )

    def test_clone(self):
        layer = LayerFactory(group=LayerGroupFactory())
        style_image = StyleImageFactory()
        layer.main_style = {"symbol": {"image": style_image.slug}}
        layer.save()
        clone = layer.make_clone()
        # clone should have "Copy" in name
        self.assertEqual(clone.name, f"{layer.name} (Copy)")
        # extra styles should be copied
        self.assertEqual(clone.extra_styles.count(), layer.extra_styles.count())
        # layer group should not be defined (excluded by default from any view)
        self.assertIsNone(clone.group)


class LayerGroupTestCase(TestCase):
    def test_str_with_parent(self):
        group1 = LayerGroupFactory()
        group2 = LayerGroupFactory(parent=group1, view=group1.view)
        self.assertEqual(
            str(group2),
            f"{group2.view.name} - {group1.label} - {group2.label}",
        )

    def test_str_without_parent(self):
        group = LayerGroupFactory()
        self.assertEqual(str(group), f"{group.view.name} - {group.label}")


class ReportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory.create()
        field = cls.report.config.layer.source.fields.create(
            name="test_field", label="test_label", data_type=FieldTypes.String.value
        )
        cls.report_field = ReportField.objects.create(
            config=cls.report.config,
            order=1,
            field=field,
        )

    def test_models_str(self):
        self.assertEqual(str(self.report), f"Report {self.report.pk}")
        self.assertEqual(str(self.report.status.label), _("New"))
        self.assertEqual(str(self.report.config), self.report.config.label)
        self.assertEqual(
            str(self.report.config.report_fields.first()),
            f"Report field {self.report_field.order}",
        )


class ExtraModelsTestCase(TestCase):
    def test_str_methods(self):
        scene = Scene.objects.create(name="My Scene")
        self.assertEqual(str(scene), "My Scene")

        category = ExtentCategory.objects.create(name="Cat")
        extent = Extent.objects.create(
            name="My Extent", category=category, minLat=0, minLon=0, maxLat=0, maxLon=0
        )
        scene_extent = SceneExtent.objects.create(scene=scene, extent=extent)
        self.assertEqual(str(scene_extent), f"{scene} - {extent}")

        source = PostGISSourceFactory(name="src_cs")
        layer = LayerFactory(main_field__source=source)
        layer.source = source
        layer.save()
        cs = CustomStyle.objects.create(layer=layer, source=source)
        self.assertEqual(
            str(cs), f"{layer.name} - {source.name} - {cs.layer_identifier}"
        )

        f = source.fields.create(name="f1", label="Field 1")
        ff = FilterField.objects.create(field=f, layer=layer, label="Filter 1")
        self.assertEqual(str(ff), "Filter 1")

        img = StyleImage.objects.create(name="icon.png")
        self.assertEqual(str(img), "icon.png")

    def test_replace_source_dry_run_and_apply(self):
        source1 = PostGISSourceFactory(name="source1")
        f1 = source1.fields.create(name="old_col", label="Old Col")
        f_del = source1.fields.create(name="deleted_col", label="Del Col")

        source2 = PostGISSourceFactory(name="source2")
        source2.fields.create(name="new_col", label="New Col")
        source2.fields.create(name="brand_new_col", label="Brand New")

        layer = LayerFactory(main_field__source=source1)
        layer.source = source1
        layer.save()
        FilterField.objects.create(field=f1, layer=layer)
        FilterField.objects.create(field=f_del, layer=layer)

        # dry_run=True
        layer.replace_source(
            source2, fields_matches={"old_col": "new_col"}, dry_run=True
        )
        self.assertEqual(layer.source, source1)

        # dry_run=False
        layer.replace_source(
            source2, fields_matches={"old_col": "new_col"}, dry_run=False
        )
        self.assertEqual(layer.source, source2)
        field_names = [ff.field.name for ff in layer.fields_filters.all()]
        self.assertIn("new_col", field_names)
        self.assertIn("brand_new_col", field_names)
        self.assertNotIn("deleted_col", field_names)

    def test_save_preserve_legend_style_dropped(self):
        source = PostGISSourceFactory(name="source_legend")
        layer = LayerFactory(main_field__source=source)
        layer.source = source
        layer.save()
        layer.legends = [{"uid": "dropped_uid__color", "title": "Legend", "auto": True}]
        layer.main_style = {"style": {}}
        layer.save(preserve_legend=True)
        self.assertEqual(layer.legends, [])
