import requests
from django.contrib.gis.gdal import DataSource
from django.core.files.temp import NamedTemporaryFile

from project.geosource.management.commands.helpers import DSCommandSource


class Command(DSCommandSource):
    def get_data_source(self):
        with NamedTemporaryFile() as temp_file:
            self.stdout.write("Start download")
            r = requests.get(
                "https://france-geojson.gregoiredavid.fr/repo/regions.geojson",
                allow_redirects=True,
            )
            temp_file.write(r.content)
            return DataSource(temp_file.name)
