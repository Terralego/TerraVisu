from django.apps import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.geosource"
    verbose_name = "Geosource"

    def ready(self):
        from django.contrib.contenttypes.models import ContentType

        from project.accounts.models import FunctionalPermission
        from project.geosource.models import Source

        # get or create functionnal permissions
        FunctionalPermission.objects.update_or_create(
            codename="can_manage_sources",
            content_type=ContentType.objects.get_for_model(Source),
            defaults={
                "name": "Can manage sources",
                "module": "DataSource",
            },
        )
