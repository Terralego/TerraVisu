from constance import config
from django.contrib.admin import AdminSite
from django.utils.translation import gettext as _


class ConfigSite(AdminSite):
    site_header = _(f"{config.INSTANCE_TITLE}: {_('Configuration')}")
    site_title = _(f"{config.INSTANCE_TITLE}: {_('Configuration')}")
    index_title = _(f"Welcome to {config.INSTANCE_TITLE} configuration interface.")


config_site = ConfigSite(name="config_site")
