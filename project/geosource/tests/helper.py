from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


def get_file(file_name):
    with open(
        settings.BASE_DIR / "geosource" / "tests" / "data" / file_name, "rb+"
    ) as f:
        return SimpleUploadedFile(f.name, f.read())
