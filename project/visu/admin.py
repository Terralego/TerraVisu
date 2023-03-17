from django.contrib import admin

from project.visu.models import ExtraMenuItem, SpriteValue


@admin.register(ExtraMenuItem)
class ExtraMenuItemAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "href", "icon")


admin.site.register(SpriteValue)
