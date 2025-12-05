import os
import shutil
from tempfile import NamedTemporaryFile
from unittest import mock

from django.apps import apps
from django.conf import settings
from django.db import connection
from django.test import TestCase

from ...management.commands.migrate import load_sql_files


class ExtraSQLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.exists(os.path.join(settings.VAR_DIR, "conf", "extra_sql")):
            os.mkdir(os.path.join(settings.VAR_DIR, "conf", "extra_sql"))

    def test_custom_sql(self):
        tmp_file = NamedTemporaryFile(
            suffix=".sql",
            prefix="test_",
            mode="w+",
            dir=os.path.join(settings.VAR_DIR, "conf", "extra_sql"),
        )
        tmp_file.write("""
        CREATE FUNCTION test() RETURNS char SECURITY DEFINER AS $$
        BEGIN
            RETURN 'test';
        END;
        $$ LANGUAGE plpgsql;
        """)
        tmp_file.flush()
        app = apps.get_app_config("terra_layer")
        load_sql_files(app, "test")
        tmp_file.close()

        cursor = connection.cursor()
        cursor.execute("""
        SELECT public.test();
        """)
        result = cursor.fetchall()
        tmp_file.close()
        self.assertEqual(result[0][0], "test")

    @mock.patch("traceback.print_exc")
    def test_failed_custom_sql(self, mock_traceback):
        with self.assertLogs(
            "project.terra_layer.management.commands.migrate", "CRITICAL"
        ) as cm:
            tmp_file = NamedTemporaryFile(
                suffix=".sql",
                prefix="test_",
                mode="w+",
                dir=os.path.join(settings.VAR_DIR, "conf", "extra_sql"),
            )
            tmp_file.write("""
            ERROR SQL
            """)
            tmp_file.flush()
            app = apps.get_app_config("terra_layer")
            with self.assertRaisesRegex(Exception, 'syntax error at or near "ERROR"'):
                load_sql_files(app, "test")
            self.assertTrue(
                f"Failed to install custom SQL file '{tmp_file.name}': syntax error at or near \"ERROR\""
                in cm.output[0]
            )
            tmp_file.close()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(os.path.join(settings.VAR_DIR, "conf", "extra_sql"))
