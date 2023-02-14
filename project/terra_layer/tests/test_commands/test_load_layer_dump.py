import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from project.geosource.models import Field, PostGISSource
from project.terra_layer.models import FilterField, Layer, Scene

UserModel = get_user_model()


class LayerDumpTestCase(TestCase):
    def setUp(self):
        self.file = os.path.join(
            "project", "terra_layer", "tests", "test_commands", "data", "data.json"
        )
        source = PostGISSource.objects.create(
            name="test",
            db_name="test",
            db_password="test",
            db_host="localhost",
            geom_type=1,
            refresh=-1,
        )
        self.field = Field.objects.create(source=source, name="toto")
        self.scene = Scene.objects.create(name="test_scene")
        self.layer = Layer.objects.create(
            source=source,
            name="Layer_with_custom_style",
            uuid="91c60192-9060-4bf6-b0de-818c5a362d89",
        )
        FilterField.objects.create(label="Test", field=self.field, layer=self.layer)

    def test_command_launch(self):
        self.maxDiff = None
        call_command("layer_load_dump", "-file={}".format(self.file))
        self.assertEqual(Layer.objects.count(), 1)

    def test_command_launch_wrong_uuid(self):
        self.maxDiff = None
        self.layer.uuid = "91c60192-9060-4bf6-b0de-818c5a362d88"
        self.layer.save()
        call_command("layer_load_dump", "-file={}".format(self.file))
        self.assertEqual(Layer.objects.count(), 2)

    def test_command_launch_command_error(self):
        file = os.path.join(
            "project", "terra_layer", "tests", "test_commands", "data", "wrong.json"
        )
        self.maxDiff = None
        self.layer.uuid = "91c60192-9060-4bf6-b0de-818c5a362d88"
        self.layer.save()
        with self.assertRaises(CommandError) as e:
            call_command("layer_load_dump", "-file={}".format(file))
        self.assertEqual(
            str(e.exception),
            "A validation error occurred with data: "
            "{'order': [ErrorDetail(string='A valid integer is required.', "
            "code='invalid')]}",
        )

    def test_command_launch_multiple_name_found(self):
        self.maxDiff = None
        self.scene.tree = [
            {"label": "layer1", "group": True, "expanded": True, "children": []},
        ]
        self.scene.save()
        file = os.path.join(
            "project",
            "terra_layer",
            "tests",
            "test_commands",
            "data",
            "multiple_name.json",
        )
        call_command("layer_load_dump", "-file={}".format(file))
        self.scene.refresh_from_db()
        new_layer = Layer.objects.exclude(name="Layer_with_custom_style").get()
        self.assertEqual(
            self.scene.tree,
            [
                {
                    "group": True,
                    "label": "layer1",
                    "children": [
                        {
                            "group": True,
                            "label": "layer2",
                            "children": [{"label": "layer3", "geolayer": new_layer.pk}],
                        }
                    ],
                    "expanded": True,
                }
            ],
        )
