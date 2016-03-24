
class Point(object):
    """ Represents a single point on a geopgrahic coordinate system. """

    def __init__(self, lat=None, lon=None):
        self.lat = lat
        self.lon = lon

    def __bool__(self):
        return (self.lat and self.lon) and True or False

    @property
    def lat(self):
        return self._lat

    @property
    def lon(self):
        return self._lon

    @lat.setter
    def lat(self, value):
        self._lat = float(value) if value else None

    @lon.setter
    def lon(self, value):
        self._lon = float(value) if value else None

    @classmethod
    def from_text(cls, text):
        lat, lon = [float(p) for p in text.split('/')]
        return cls(lat=lat, lon=lon)

    def as_text(self):
        if self:
            return '/'.join(str(p) for p in (self.lat, self.lon))
        else:
            return ''
