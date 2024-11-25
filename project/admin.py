from django.contrib.admin import AdminSite
from django.utils.translation import gettext as _


class ConfigSite(AdminSite):
    site_header = _("TerraVisu: Configuration")
    site_title = _("TerraVisu: Configuration")
    index_title = _("Welcome to TerraVisu configuration interface.")


config_site = ConfigSite(name="config_site")
