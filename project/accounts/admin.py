from constance import config
from django.contrib import admin

from project.accounts.models import FunctionalPermission, User

admin.site.register(User)
admin.site.register(FunctionalPermission)
admin.site.site_header = f"{config.INSTANCE_TITLE} configuration"
