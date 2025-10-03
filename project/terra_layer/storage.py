from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs["location"] = str(settings.PRIVATE_MEDIA_ROOT)
        kwargs["base_url"] = "private"
        super().__init__(*args, **kwargs)


private_media_storage = PrivateMediaStorage()
