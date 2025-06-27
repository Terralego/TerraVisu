import json
from io import StringIO
from unittest import mock

import freezegun
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from project.geosource.models import Field, PostGISSource
from project.terra_layer.models import CustomStyle, FilterField, Layer

UserModel = get_user_model()


class LayerDumpTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = PostGISSource.objects.create(
            name="test_view",
            db_name="test",
            db_password="test",
            db_host="localhost",
            geom_type=1,
            refresh=-1,
        )

    @freezegun.freeze_time("2020-01-01 00:00:00")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_command_launch_without_custom_style(self, mock_sdout):
        self.maxDiff = None
        layer = Layer.objects.create(
            source=self.source,
            name="Layer_without_custom_style",
            uuid="91c60192-9060-4bf6-b0de-818c5a362d89",
        )
        call_command("layer_dump", pk=layer.pk)
        self.assertDictEqual(
            json.loads(mock_sdout.getvalue()),
            {
                "fields": [],
                "extra_styles": [],
                "advanced_style": {},
                "compare_field": None,
                "compare_separator": "",
                "compare_url": "",
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2020-01-01T00:00:00Z",
                "uuid": "91c60192-9060-4bf6-b0de-818c5a362d89",
                "name": "Layer_without_custom_style",
                "source_filter": "",
                "in_tree": True,
                "order": 0,
                "description": "",
                "main_style": {},
                "layer_style": {},
                "layer_style_wizard": {},
                "settings": {},
                "active_by_default": False,
                "legends": [],
                "table_enable": False,
                "table_export_enable": False,
                "popup_config": {},
                "minisheet_config": {},
                "interactions": [],
                "report_configs": [],
                "source": "test_view",
                "group": None,
                "main_field": None,
                "view": None,
                "style_images": [],
                "variables": [],
            },
        )

    def test_command_fail(self):
        out = StringIO()
        with self.assertRaisesRegex(CommandError, "Layer does not exist"):
            call_command("layer_dump", pk=999, stdout=out)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_command_launch(self, mock_stdout):
        layer = Layer.objects.create(
            source=self.source,
            name="Layer_with_extra_style",
            interactions=[
                {
                    "id": "terralego-eae-sync",
                    "interaction": "highlight",
                    "trigger": "mouseover",
                },
            ],
            minisheet_config={
                "enable": True,
                "highlight_color": True,
            },
            popup_config={"enable": True},
        )
        CustomStyle.objects.create(
            layer=layer,
            source=self.source,
            interactions=[
                {"id": "extra_style", "interaction": "highlight", "trigger": "click"},
            ],
        )
        call_command("layer_dump", pk=layer.pk)
        self.assertEqual(
            json.loads(mock_stdout.getvalue())["extra_styles"],
            [
                {
                    "style_config": {},
                    "style": {},
                    "interactions": [
                        {
                            "id": "extra_style",
                            "trigger": "click",
                            "interaction": "highlight",
                        }
                    ],
                    "source": "test_view",
                }
            ],
        )

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_command_launch_with_filer_field(self, mock_stdout):
        field = Field.objects.create(source=self.source, name="tutu")

        layer = Layer.objects.create(
            source=self.source,
            name="Layer_with_extra_style",
            interactions=[
                {
                    "id": "terralego-eae-sync",
                    "interaction": "highlight",
                    "trigger": "mouseover",
                },
            ],
            minisheet_config={
                "enable": True,
                "highlight_color": True,
            },
            popup_config={"enable": True},
        )
        FilterField.objects.create(label="Test", field=field, layer=layer)
        call_command("layer_dump", pk=layer.pk)
        self.assertEqual(
            json.loads(mock_stdout.getvalue())["fields"],
            [
                {
                    "exportable": False,
                    "display": True,
                    "settings": {},
                    "field": "tutu",
                    "filter_enable": False,
                    "filter_settings": {},
                    "format_type": "",
                    "label": "Test",
                    "order": 0,
                    "shown": False,
                }
            ],
        )
