from django.core.management import BaseCommand

from project.geosource.periodics import auto_refresh_source


class Command(BaseCommand):
    help = "Launch resync of all sources if needed"

    def handle(self, *args, **options):
        auto_refresh_source()
