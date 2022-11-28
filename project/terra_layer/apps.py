from django.apps import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.terra_layer"
    verbose_name = "ViewLayer"

    def ready(self):
        from django.contrib.contenttypes.models import ContentType

        from project.accounts.models import FunctionalPermission
        from project.terra_layer.models import Layer

        # get or create functional permissions
        FunctionalPermission.objects.update_or_create(
            codename="can_manage_layers",
            content_type=ContentType.objects.get_for_model(Layer),
            defaults={
                "name": "Can manage layers",
                "module": "DataLayer",
            },
        )
