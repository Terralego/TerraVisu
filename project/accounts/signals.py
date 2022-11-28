import logging

logger = logging.getLogger(__name__)


def permission_callback(sender, **kwargs):
    logger.info(f"Updating permissions of {sender.name}")

    ContentType = sender.apps.get_model("contenttypes.ContentType")
    TerraPermission = sender.apps.get_model("accounts.FunctionalPermission")

    for module, perm, name in sender.permissions:
        content_type = ContentType.objects.get_for_model(TerraPermission)

        TerraPermission.objects.update_or_create(
            content_type=content_type,
            codename=perm,
            defaults={"name": name, "module": module},
        )
