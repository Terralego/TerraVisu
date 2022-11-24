import json

from rest_framework import parsers


class NestedMultipartJSONParser(parsers.MultiPartParser):
    """
    Parser for processing multipart with json content
    """

    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(
            stream=stream, media_type=media_type, parser_context=parser_context
        )

        data = {}
        for key, value in result.data.items():
            try:
                data[key] = json.loads(value)
            except json.JSONDecodeError:
                data[key] = value

        return parsers.DataAndFiles(data, result.files)
