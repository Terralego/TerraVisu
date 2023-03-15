from project.geosource.management.commands.helpers import DSCommandSource


class Command(DSCommandSource):
    data_source_path = "/opt/terra-visu/project/geosource/tests/data/test.geojson"
