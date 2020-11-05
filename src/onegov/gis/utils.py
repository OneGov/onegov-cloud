import requests
from purl import URL

from onegov.gis import Coordinates


class MapboxRequests():

    endpoints = ('places', )

    def __init__(self, access_token, locale=None):
        self.access_token = access_token

    def base_url(self, endpoint):
        assert endpoint in self.endpoints
        url = URL(f'https://api.mapbox.com/geocoding/v5/mapbox.{endpoint}')
        url = url.query_param('access_token', self.access_token)
        return url

    def geocode_address_url(self, text=None, street=None, zip_code=None, city=None,
                        ctry=None, locale=None):
        if not ctry:
            ctry = 'Schweiz'

        if not text:
            assert street
            assert zip_code
            assert city

        address = text or f'{street}, {zip_code} {city}, {ctry}'

        url = self.base_url('places')
        url = url.add_path_segment(f'{address}.json')
        url = url.query_param('types', 'address')

        locale = locale and locale.replace('_CH', '')
        if locale:
            url = url.query_param('language', locale)
        return url

    def geocode_address(self, text=None, street=None, zip_code=None, city=None,
                        ctry=None, locale=None):

        url = self.geocode_address_url(
            text, street, zip_code, city, ctry, locale)

        result = requests.get(url.as_string())

        if result.status_code != 200:
            return

        data = result.json()
        coordinates = None
        for feature in data['features']:
            matched_place = feature.get('matching_place_name')
            if not matched_place:
                continue
            place_types = feature['place_type']
            if 'address' not in place_types:
                continue
            if zip_code and str(zip_code) not in matched_place:
                continue
            x, y = feature['geometry']['coordinates']
            return Coordinates(lat=x, lon=y)

        return coordinates

