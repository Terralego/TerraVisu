from django.core.management import BaseCommand

from project.geosource.models import Source


class Command(BaseCommand):
    help = "Launch resync of all available sources"

    def add_arguments(self, parser):
        parser.add_argument(
            "-pk", type=int, action="store", help="Pk of the source to sync"
        )
        parser.add_argument(
            "--sync", dest="sync", action="store_true", help="Run in sync"
        )

    def handle(self, *args, **options):
        source = Source.objects.get(id=options["pk"])
        if options["sync"]:
            print(f"Refreshing source {source}<{source.id}>...")
            source.refresh_data()
        else:
            print(f"Schedule refresh for source {source}<{source.id}>...")
            source.run_async_method("refresh_data")
