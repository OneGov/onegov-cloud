class Coordinates(object):
    """ Represents a pair of coordinates.

    May contain zoom factor and other information like marker icon and
    color. Note that only latitude and longitude really matter, the rest
    may or may not be used.

    """

    def __init__(self, lat=None, lon=None, zoom=None):
        self.lat = lat
        self.lon = lon
        self.zoom = zoom

    def __bool__(self):
        return False if None in (self.lat, self.lon) else True

    def as_dict(self):
        return {
            'lat': self.lat,
            'lon': self.lon,
            'zoom': self.zoom
        }


class CoordinatesMixin(object):
    """ Extends any class that has a content dictionary field with a single
    coordinates pair.

    """

    @property
    def coordinates(self):
        return Coordinates(**self.content.get('coordinates', {}))

    @coordinates.setter
    def coordinates(self, value):
        if value is None:
            value = {}

        if not isinstance(value, dict):
            value = value.as_dict()

        self.content['coordinates'] = value
