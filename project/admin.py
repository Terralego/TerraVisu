from django.contrib.admin import AdminSite
from django.utils.translation import gettext as _

from project.terra_layer.admin import ReportAdmin
from project.terra_layer.models import Report


class ConfigSite(AdminSite):
    site_header = _("TerraVisu: Configuration")
    site_title = _("TerraVisu: Configuration")
    index_title = _("Welcome to TerraVisu configuration interface.")


config_site = ConfigSite(name="config_site")
config_site.register(Report, ReportAdmin)
