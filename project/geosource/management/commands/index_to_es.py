from django.core.management import BaseCommand
from geostore.models import Layer

from project.geosource.elasticsearch import ESMixin
from project.geosource.elasticsearch.index import LayerESIndex

EXCLUDED_FIELDS = ()
GEOMETRY_FIELD = "geom"


class Command(BaseCommand):
    """This is the ETL for indexing features in elasticsearch"""

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            "--layer", type=int, help="Index only a layer with pk", required=False
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Indexing layers to ES..."))
        client = ESMixin.get_client()
        if options["layer"] is not None:
            qs = Layer.objects.filter(pk=options["layer"])
        else:
            self.stdout.write("... Indexing all layers...")
            qs = Layer.objects.all()
        qs = qs.prefetch_related("features")
        for layer in qs:
            self.stdout.write(f"... Indexing layer {layer}")
            layer_indexation = LayerESIndex(layer, client=client)
            layer_indexation.index()
