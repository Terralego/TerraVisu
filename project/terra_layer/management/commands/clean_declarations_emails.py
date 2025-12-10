from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from project.terra_layer.models import Declaration


class Command(BaseCommand):
    help = "Clear email field for declarations created more than a year ago"

    def handle(self, *args, **options):
        one_year_ago = timezone.now() - timedelta(days=365)
        updated_count = Declaration.objects.filter(created_at__lt=one_year_ago).update(
            email=""
        )

        self.stdout.write(f"Cleared email field for {updated_count} declarations")
