from django.apps import AppConfig as BaseAppConfig

from project.accounts.permission_mixins import PermissionRegistrationMixin


class AppConfig(PermissionRegistrationMixin, BaseAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.geosource"
    verbose_name = "Geosource"
    permissions = (("DataSource", "can_manage_sources", "Can manage sources"),)
