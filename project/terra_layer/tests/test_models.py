from django.test import TestCase

from project.geosource.models import PostGISSource
from project.terra_layer.models import Layer

from .factories import LayerFactory, SceneFactory


class LayerTestCase(TestCase):
    def test_str(self):
        source = PostGISSource.objects.create(
            name="test",
            db_name="test",
            db_password="test",
            db_host="localhost",
            geom_type=1,
            refresh=-1,
        )
        layer = Layer.objects.create(
            source=source,
            name="foo",
            uuid="91c60192-9060-4bf6-b0de-818c5a362d89",
        )
        self.assertEqual(str(layer), "Layer({}) - foo".format(layer.pk))

    def test_scene_insert_in_tree(self):
        scene = SceneFactory()

        source = PostGISSource.objects.create(
            name="test",
            db_name="test",
            db_password="test",
            db_host="localhost",
            geom_type=1,
            refresh=-1,
        )

        # Initial value
        self.assertEqual(scene.tree, [])

        layer = LayerFactory(source=source)
        layer2 = LayerFactory(source=source)
        layer3 = LayerFactory(source=source)
        layer4 = LayerFactory(source=source)

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
