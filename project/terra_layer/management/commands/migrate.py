import logging
import re
import traceback
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.commands.migrate import Command as BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


def load_sql_files(app, stage):
    """
    Look for SQL files in Django app, and load them into database.
    """
    sql_dir = Path(app.path) / "sql"
    custom_sql_dir = Path(settings.VAR_DIR) / "conf" / "extra_sql"
    sql_files = []
    r = re.compile(rf"^{stage}_.*\.sql$")

    if sql_dir.exists():
        sql_files += [
            str(f)
            for f in sql_dir.iterdir()
            if f.is_file() and r.match(f.name) is not None
        ]

    if custom_sql_dir.exists():
        sql_files += [
            str(f)
            for f in custom_sql_dir.iterdir()
            if f.is_file() and r.match(f.name) is not None
        ]

    sql_files.sort()
    cursor = connection.cursor()

    for sql_file in sql_files:
        try:
            logger.debug("Loading initial SQL data from '%s'", sql_file)
            sql_path = Path(sql_file)
            rendered_sql = sql_path.read_text()
            cursor.execute(rendered_sql)
        except Exception as e:
            logger.critical("Failed to install custom SQL file '%s': %s\n", sql_file, e)
            traceback.print_exc()
            raise


class Command(BaseCommand):
    def handle(self, *args, **options):
        for app in apps.get_app_configs():
            load_sql_files(app, "pre")
        super().handle(*args, **options)
        for app in apps.get_app_configs():
            load_sql_files(app, "post")
