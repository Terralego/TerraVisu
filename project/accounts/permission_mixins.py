from django.db.models.signals import post_migrate

from .signals import permission_callback


class PermissionRegistrationMixin:
    permissions = ()

    def ready(self):
        super().ready()
        post_migrate.connect(permission_callback, sender=self)
