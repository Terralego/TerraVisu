import logging

logger = logging.getLogger(__name__)


def permission_callback(sender, **kwargs):
    logger.info(f"Updating permissions of {sender.name}")

    ContentType = sender.apps.get_model("contenttypes.ContentType")
    FunctionalPermission = sender.apps.get_model("accounts.FunctionalPermission")
    content_type = ContentType.objects.get_for_model(FunctionalPermission)

    for module, perm, name in sender.permissions:
        FunctionalPermission.objects.update_or_create(
            content_type=content_type,
            codename=perm,
            defaults={"name": name, "module": module},
        )
