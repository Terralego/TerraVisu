from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from project.accounts.models import FunctionalPermission, PermanentAccessToken, User
from project.admin import config_site

admin.site.index_title = f"TerraVisu: {_('Debug panel')}"
admin.site.site_header = f"TerraVisu: {_('Debug panel')}"
admin.site.index_title = _("Welcome to TerraVisu debug interface.")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (_("Personal info"), {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_report_manager",
                    "is_declaration_manager",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ("date_joined",)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_report_manager",
        "is_declaration_manager",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "uuid")
    ordering = ("email",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )


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
