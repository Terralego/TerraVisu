from constance import config
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from project.accounts.models import FunctionalPermission, PermanentAccessToken, User
from project.admin import config_site

admin.site.index_title = f'{config.INSTANCE_TITLE}: {_("Debug panel")}'
admin.site.site_header = f'{config.INSTANCE_TITLE}: {_("Debug panel")}'
admin.site.index_title = _(f"Welcome to {config.INSTANCE_TITLE} debug interface.")

admin.site.register(User)


@admin.register(FunctionalPermission)
class FunctionalPermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "codename", "module")
    search_fields = ("name", "codename", "module")
    list_filter = ("module",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PermanentAccessToken, site=config_site)
class PermanentAccessTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    list_filter = ("user", "created_at", "updated_at")
    search_fields = ("user__email", "token")
    readonly_fields = ("token",)
