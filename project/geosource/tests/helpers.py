import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


def get_file(file_name):
    try:
        file_path = settings.BASE_DIR / "geosource" / "tests" / "data" / file_name
        with open(
            file_path, "rb+"
        ) as f:
            return SimpleUploadedFile(f.name, f.read())
    except PermissionError:
        raise Exception(f"Permission denied to read file {os.stat(file_path)}")
