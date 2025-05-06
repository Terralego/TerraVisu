import json

from django.core.management.base import BaseCommand, CommandError

from project.geosource.models import Field, Source
from project.terra_layer.models import Layer, LayerGroup, Scene
from project.terra_layer.serializers import LayerDetailSerializer


class Command(BaseCommand):
    help = "Dump a layer to json format"

    def add_arguments(self, parser):
        parser.add_argument(
            "-pk", type=int, action="store", help="Pk of the layer to export"
        )

    def handle(self, *args, **options):
        try:
            self.layer = Layer.objects.get(pk=options.get("pk"))
        except Layer.DoesNotExist:
            msg = "Layer does not exist"
            raise CommandError(msg)

        serialized = LayerDetailSerializer(self.layer).data
        self.clean_ids(serialized)

        self.stdout.write(json.dumps(serialized))

    def clean_ids(self, serialized):
        excluded_fields = ("id",)
        for field in excluded_fields:
            serialized.pop(field)

        # Clean custom_style id
        for cs in serialized.get("extra_styles", []):
            cs.pop("id")
            cs["source"] = Source.objects.get(pk=cs["source"]).slug

        for field in serialized.get("fields", []):
            field.pop("id")
            field.pop("sourceFieldId")
            field["field"] = Field.objects.get(pk=field["field"]).name

        fk_fields = (
            (LayerGroup, "group", "label"),
            (Scene, "view", "slug"),
            (Source, "source", "slug"),
            (Field, "main_field", "name"),
        )

        for klass, field, sfield in fk_fields:
            if serialized.get(field):
                serialized[field] = getattr(
                    klass.objects.get(pk=serialized.get(field)), sfield
                )
