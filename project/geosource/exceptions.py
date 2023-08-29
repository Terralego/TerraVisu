class SourceException(Exception):
    """Generic source exception to be catched by the generic Source Model"""

    def __init__(self, message):
        self.message = message


class CSVSourceException(SourceException):
    """CSVSource exception raised by the CSVSource model"""

    pass


class GeoJSONSourceException(SourceException):
    """GeoJSONSource exception raised by the GeoJSONSourec model"""

    pass
