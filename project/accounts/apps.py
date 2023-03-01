from django.apps import AppConfig as BaseAppConfig
from django.utils.translation import gettext_lazy as _

from project.accounts.permission_mixins import PermissionRegistrationMixin


class AppConfig(PermissionRegistrationMixin, BaseAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.accounts"
    verbose_name = "Accounts"

    permissions = (
        ("User", "can_manage_users", _("Is able to create, delete, update users")),
        (
            "UserGroup",
            "can_manage_groups",
            _("Is able to create, delete, update groups"),
        ),
        ("DataLayer", "can_manage_layers", _("Can manage layers")),
        ("DataSource", "can_manage_sources", _("Can manage sources")),
        ("BaseLayer", "can_manage_baselayers", _("Can manage base map layers")),
    )
