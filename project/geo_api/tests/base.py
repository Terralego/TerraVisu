from django.db import connection
from django.test import TestCase


class BaseGeoAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
