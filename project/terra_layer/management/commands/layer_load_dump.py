import argparse
import json

from django.core.management.base import BaseCommand, CommandError

from project.geosource.models import Source
from project.terra_layer.models import Layer, Scene
from project.terra_layer.serializers import LayerDetailSerializer


class Command(BaseCommand):
    help = "Load a dumped layer"

    def add_arguments(self, parser):
        parser.add_argument(
            "-file",
            type=argparse.FileType("r"),
            required=True,
            action="store",
            help="json file path",
        )

    def handle(self, *args, **options):
        data = json.load(options["file"])

        source = Source.objects.get(slug=data["source"])

        fk_fields = (
            (Scene, "view", "slug"),
            (Source, "source", "slug"),
        )

        for klass, field, sfield in fk_fields:
            if data.get(field):
                data[field] = klass.objects.get(**{sfield: data[field]}).pk

        for cs in data["extra_styles"]:
            cs["source"] = Source.objects.get(slug=cs["source"]).pk

        if data.get("main_field"):
            data["main_field"] = source.fields.get(name=data["main_field"]).pk

        for field in data["fields"]:
            field["field"] = source.fields.get(name=field["field"]).pk

        parts = data["name"].split("/")
        layer_name = parts.pop()

        # Try to find already existing layer
        try:
            layer = Layer.objects.get(uuid=data["uuid"])
            exists = True
        except Exception:
            layer = Layer()
            exists = False

        del data["group"]  # Remove group as we compute it later
        data["name"] = layer_name

        layer_detail_serializer = LayerDetailSerializer(instance=layer, data=data)
        try:
            layer_detail_serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise CommandError(f"A validation error occurred with data: {e}")

        layer_detail_serializer.save()

        # Here we insert layer in tree if not previously existing
        if not exists:
            scene = Scene.objects.get(id=data["view"])
            scene.insert_in_tree(layer_detail_serializer.instance, parts)
