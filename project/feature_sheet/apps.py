from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FeatureSheetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.feature_sheet"
    verbose_name = _("Feature sheet")
