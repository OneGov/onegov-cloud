from onegov.gis.utils import MapboxRequests

valid_address = 'Pilatusstrasse 3, 6003 Luzern, Schweiz'
luzern = (47.04575, 8.309)
luzern_2 = (47.05646, 8.29394)


def test_mapbox_requests():
    token = 'a_token'
    host = MapboxRequests.host
    api = MapboxRequests(token, endpoint='geocoding', profile='places')
    assert api.base_url.as_string() == \
           f'{host}/geocoding/v5/mapbox.places?access_token={token}'

    geocode_url = api.geocode(valid_address, as_url=True).as_string()
    assert geocode_url == \
           f'{host}/geocoding/v5/mapbox.places/' \
           f'Pilatusstrasse%203%2C%206003%20Luzern%2C%20Schweiz.json' \
           f'?access_token={token}&types=address'

    api = MapboxRequests(token, endpoint='directions', profile='driving')
    assert api.base_url.as_string() == \
           f'{host}/directions/v5/mapbox/driving?access_token={token}'

    url = api.directions([luzern, luzern_2], as_url=True)
    print(url.as_string())
    assert url.as_string() == \
           f'{host}/directions/v5/mapbox/driving/{luzern[0]},{luzern[1]};' \
           f'{luzern_2[0]},{luzern_2[1]}?access_token={token}'.\
               replace(',', '%2C').replace(';', '%3B')

