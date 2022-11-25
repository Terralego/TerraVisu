from django.apps import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.visu"
    verbose_name = "Visu"
