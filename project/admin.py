import copy

from django.contrib.admin import AdminSite
from django.utils.translation import gettext as _

from project.visu.models import FeatureSheet, SheetBlock, SheetField


class ConfigSite(AdminSite):
    site_header = _("TerraVisu: Configuration")
    site_title = _("TerraVisu: Configuration")
    index_title = _("Welcome to TerraVisu configuration interface.")

    def move_models_to_new_app(self, apps, models, old_app, new_app):
        for app_config in apps:
            if app_config["name"] == old_app:
                # Copy app config, with empty models
                new_app_config = copy.deepcopy(app_config)
                new_app_config["name"] = new_app
                new_app_config["models"] = []
                for model_config in copy.deepcopy(app_config["models"]):
                    # Remove selected models from old app, and put them in new app
                    if model_config["model"] in models:
                        new_app_config["models"].append(model_config)
                        app_config["models"].remove(model_config)
                apps.append(new_app_config)
        return apps

    def get_app_list(self, request):
        apps = super().get_app_list(request)
        self.move_models_to_new_app(
            apps, [FeatureSheet, SheetField, SheetBlock], "Visu", _("Feature sheets")
        )
        return apps


config_site = ConfigSite(name="config_site")
