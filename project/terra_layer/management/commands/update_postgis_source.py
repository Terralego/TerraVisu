import csv

from django.core.management.base import BaseCommand

from project.geosource.models import Source
from project.terra_layer.models import Layer


class Command(BaseCommand):
    help = "update a given layer with a given Source"

    def add_arguments(self, parser):
        parser.add_argument("layer", type=int, help="pk of the layer")
        parser.add_argument("source", action="store", help="name of the new source")
        parser.add_argument(
            "--matches",
            action="store",
            help="optionnal csv file, separated with a comma, with field matching between sources",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="dry run with actions outputed instead",
        )

    def handle(self, **options):
        layer_id = options.get("layer")
        source_name = options.get("source")
        matches = options.get("matches")
        dry_run = options.get("dry_run")

        if not Layer.objects.filter(id=layer_id).exists():
            self.stdout.write(self.style.ERROR(f"Layer {layer_id} does not exists"))
            return

        fields_matches = {}
        if matches:
            with open(matches, "r") as f:
                reader = csv.reader(f, delimiter=",")
                for row in reader:
                    old_name, new_name = row
                    fields_matches[old_name] = new_name

        layer = Layer.objects.get(id=layer_id)
        source = Source.objects.get(name=source_name)
        layer.replace_source(source, fields_matches, dry_run)
