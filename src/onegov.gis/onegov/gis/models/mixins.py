class MapPointMixin(object):
    """ Extends any class that has a content dictionary field with a single
    lat/lon point.

    """

    @property
    def lat(self):
        return self.content.get('lat')

    @property
    def lon(self):
        return self.content.get('lon')

    @lat.setter
    def lat(self, value):
        self.content['lat'] = float(value)

    @lon.setter
    def lon(self, value):
        self.content['lon'] = float(value)

    @property
    def geolocation(self):
        return {
            'lat': self.lat,
            'lon': self.lon
        }
