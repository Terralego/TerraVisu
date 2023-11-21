from django.test import TestCase

from ..models import Layer
from ...geosource.tests.factories import PostGISSourceFactory
from .factories import LayerFactory, LayerGroupFactory, SceneFactory, StyleImageFactory


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
                            "children": [{"geolayer": layer.id, "label": ""}],
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
                            "children": [{"geolayer": layer.id, "label": ""}],
                        },
                        {"geolayer": layer2.id, "label": ""},
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
                            "children": [{"geolayer": layer.id, "label": ""}],
                        },
                        {"geolayer": layer2.id, "label": ""},
                    ],
                },
                {
                    "group": True,
                    "label": "level1Foo",
                    "children": [{"geolayer": layer3.id, "label": ""}],
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
                            "children": [{"geolayer": layer.id, "label": ""}],
                        },
                        {"geolayer": layer2.id, "label": ""},
                    ],
                },
                {
                    "group": True,
                    "label": "level1Foo",
                    "children": [
                        {"geolayer": layer3.id, "label": ""},
                        {
                            "group": True,
                            "label": "level2",
                            "children": [{"geolayer": layer4.id, "label": ""}],
                            "selectors": [],
                        },
                    ],
                },
            ],
        )

    def test_clone(self):
        layer = LayerFactory(group=LayerGroupFactory())
        style_image = StyleImageFactory(layer=layer)
        layer.main_style = {"symbol": {"image": style_image.slug}}
        layer.save()
        clone = layer.make_clone()
        # clone should have "Copy" in name
        self.assertEqual(clone.name, f"{layer.name} (Copy)")
        # style images and extra styles should be copied
        self.assertEqual(clone.style_images.count(), layer.style_images.count())
        self.assertEqual(clone.extra_styles.count(), layer.extra_styles.count())
        # layer group should not be defined (excluded by default from any view)
        self.assertIsNone(clone.group)
        # style image references in styles should be updated with new ones)
        self.assertNotEqual(
            style_image.slug,
            clone.main_style["symbol"]["image"],
            clone.style_images.values_list("slug", flat=True),
        )
