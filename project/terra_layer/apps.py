from django.apps import AppConfig as BaseAppConfig

from project.accounts.permission_mixins import PermissionRegistrationMixin


class AppConfig(PermissionRegistrationMixin, BaseAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.terra_layer"
    verbose_name = "ViewLayer"
    permissions = (("DataLayer", "can_manage_layers", "Can manage layers"),)
