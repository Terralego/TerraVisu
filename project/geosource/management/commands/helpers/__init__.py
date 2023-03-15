from django.contrib.gis.gdal import DataSource
from django.core.management import BaseCommand
from geostore.models import Feature

from project.geosource.models import CommandSource, Field, FieldTypes


class BaseCommandSource(BaseCommand):
    source = None
    geom_type = None

    def get_source(self, pk):
        return CommandSource.objects.get(pk=pk)

    def get_data(self):
        raise NotImplementedError

    def parse_data_to_feature(self, data):
        """
        Should return a Feature object filled by data.
        Ex: Feature(geom=data["geom"], properties=data["properties"])
        """
        raise NotImplementedError

    def update_source_fields(self, data_element):
        """
        Should update source fields with fields list
        """
        raise NotImplementedError

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=int,
            help="Source ID",
        )

    def handle(self, *args, **options):
        self.source = self.get_source(options["source"])
        self.stdout.write(f"Start refresh {self.source.name}")
        layer = self.source.get_layer()
        counter = 0
        data = self.get_data()
        if data:
            for element in data:
                if counter == 0:
                    self.update_source_fields(element)
                counter += 1
                feature = self.parse_data_to_feature(element)
                feature.layer = layer
                feature.save()
                self.stdout.write(
                    f"{counter}/{len(data)} : Feature {feature.identifier} refreshed"
                )
        self.stdout.write(f"End refresh {self.source.name}")


class DSCommandSource(BaseCommandSource):
    """Default CommandSource parsing all GDAL supported data format in django.contrib.gis.gdal.DataSource"""

    data_source_path = None

    def get_data_source(self):
        if self.data_source_path:
            return DataSource(self.data_source_path)
        raise NotImplementedError

    def update_source_fields(self, data_element):
        counter = -1
        for prop in data_element:
            counter += 1
            data_type = FieldTypes.get_type_from_data(data_element.get(prop))
            Field.objects.get_or_create(
                source=self.source,
                name=prop.name,
                defaults={
                    "label": prop.name.title(),
                    "sample": [data_element.get(prop)],
                    "data_type": data_type.value,
                    "order": counter,
                },
            )

    def parse_data_to_feature(self, data):
        properties = {}
        for prop in data.fields:
            properties[prop] = data.get(prop)
        return Feature(geom=data.geom.geos, properties=properties)

    def get_data(self):
        """by default return first layer id DS"""
        return self.get_data_source()[0]
