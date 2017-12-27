from onegov.core.custom import json


class Coordinates(json.Serializable, keys=('lon', 'lat', 'zoom')):
    """ Represents a pair of coordinates.

    May contain zoom factor and other information like marker icon and
    color. Note that only latitude and longitude really matter, the rest
    may or may not be used.

    """

    __slots__ = ('lon', 'lat', 'zoom')

    def __init__(self, lat=None, lon=None, zoom=None):
        self.lat = lat
        self.lon = lon
        self.zoom = zoom

    def __bool__(self):
        return False if None in (self.lat, self.lon) else True

    def __eq__(self, other):
        if not isinstance(other, Coordinates):
            return False

        return self.lat == other.lat and\
            self.lon == other.lon and\
            self.zoom == other.zoom


class CoordinatesMixin(object):
    """ Extends any class that has a content dictionary field with a single
    coordinates pair.

    """

    @property
    def coordinates(self):
        return self.content.get('coordinates') or Coordinates()

    @coordinates.setter
    def coordinates(self, value):
        self.content['coordinates'] = value or {}
