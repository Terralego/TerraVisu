from django.core.management import BaseCommand

from project.geosource.models import Source


class Command(BaseCommand):
    help = "Launch resync of all available sources"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            dest="force",
            action="store_true",
            help="Force sync even if already launched",
        )
        parser.add_argument(
            "--ask",
            dest="ask",
            action="store_true",
            help="Ask confirmation before syncing a source",
        )
        parser.add_argument(
            "--sync", dest="sync", action="store_true", help="Run in sync"
        )

    def handle(self, *args, **options):
        for source in Source.objects.all():
            if options["ask"]:
                resp = (
                    input(
                        f"Do you like to refresh the source {source}<{source.id}>? [y|N]"
                    )
                    or "n"
                )
            else:
                resp = "y"

            if resp.lower() == "y":
                if options["sync"]:
                    print(f"Refreshing source {source}<{source.id}>...")
                    source.refresh_data()
                else:
                    print(f"Schedule refresh for source {source}<{source.id}>...")
                    source.run_async_method("refresh_data", force=options["force"])
