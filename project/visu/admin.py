from admin_interface.admin import ThemeAdmin
from admin_interface.models import Theme
from constance.admin import Config, ConstanceAdmin
from django.contrib import admin

from project.admin import config_site
from project.visu.models import ExtraMenuItem, SpriteValue


class ExtraMenuItemAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "href", "icon")


config_site.register(SpriteValue)
config_site.register(ExtraMenuItem, ExtraMenuItemAdmin)
admin.site.unregister([Config])
config_site.register([Config], ConstanceAdmin)
admin.site.unregister(Theme)
config_site.register(Theme, ThemeAdmin)
