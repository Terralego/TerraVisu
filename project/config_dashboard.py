"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'terra-visu.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import gettext_lazy as _
from grappelli.dashboard import Dashboard, modules


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """

    def init_with_context(self, context):
        self.children.append(
            modules.ModelList(
                _("Instance customization"),
                column=1,
                collapsible=False,
                models=("constance.*", "project.visu.*"),
            )
        )
        self.children.append(
            modules.ModelList(
                _("Administration"),
                column=1,
                collapsible=True,
                models=("django.contrib.*", "project.accounts.*"),
            )
        )
        self.children.append(
            modules.AppList(
                _("Applications"),
                column=2,
                css_classes=("collapsed",),
                exclude=(
                    "django.contrib.*",
                    "project.accounts.*",
                    "constance.*",
                    "project.visu.*",
                    "django_celery_results.*",
                    "django_celery_beat.*",
                ),
            )
        )
        self.children.append(
            modules.AppList(
                _("Celery"),
                column=3,
                css_classes=("collapse closed",),
                models=("django_celery_results.*", "django_celery_beat.*"),
            )
        )
        # append a recent actions module
        self.children.append(
            modules.RecentActions(
                _("Recent actions"),
                limit=5,
                collapsible=False,
                column=3,
            )
        )
