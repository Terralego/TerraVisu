from django.contrib import admin

from project.accounts.models import FunctionalPermission, User

admin.site.register(User)
admin.site.register(FunctionalPermission)
