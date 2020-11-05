import requests
from purl import URL


class MapboxRequests():

    host = 'https://api.mapbox.com'
    endpoints = ('directions', 'geocoding')
    geocode_profiles = ('places', )
    directions_profiles = ('driving-traffic', 'driving', 'walking', 'cycling')

    def __init__(
            self,
            access_token,
            endpoint='geocoding',
            profile='mapbox.places',
            api_version='v5'
    ):
        assert endpoint in self.endpoints
        if endpoint == 'directions':
            assert profile in self.directions_profiles
            profile = f'mapbox/{profile}'
        if endpoint == 'geocoding':
            assert profile in self.geocode_profiles
            profile = f'mapbox.{profile}'

        self.access_token = access_token
        self.endpoint = endpoint
        self.profile = profile
        self.api_version = api_version

    @property
    def base_url(self):
        url = URL(f'{self.host}/{self.endpoint}/{self.api_version}/{self.profile}')
        url = url.query_param('access_token', self.access_token)
        return url

    def geocode(self, text=None, street=None, zip_code=None, city=None,
                        ctry=None, locale=None, as_url=False):
        if not ctry:
            ctry = 'Schweiz'

        if not text:
            assert street
            assert zip_code
            assert city

        address = text or f'{street}, {zip_code} {city}, {ctry}'

        url = self.base_url
        url = url.add_path_segment(f'{address}.json')
        url = url.query_param('types', 'address')

        locale = locale and locale.replace('_CH', '')
        if locale:
            url = url.query_param('language', locale)
        if as_url:
            return url
        return requests.get(url.as_string())

    def directions(self, coordinates, as_url=False):
        """
        coordinates: iterable of tuples of (lat, lon)
        """
        url = self.base_url.add_path_segment(
            ';'.join(f'{c[0]},{c[1]}' for c in coordinates)
        )
        if as_url:
            return url
        return requests.get(url.as_string())
