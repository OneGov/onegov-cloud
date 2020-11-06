from onegov.gis import Coordinates


def parse_geocode_result(response, zip_code, zoom=None):

    if response.status_code != 200:
        return

    data = response.json()
    for feature in data['features']:
        matched_place = feature.get('matching_place_name')
        if not matched_place:
            continue
        place_types = feature['place_type']
        if 'address' not in place_types:
            continue
        if zip_code and str(zip_code) not in matched_place:
            continue
        y, x = feature['geometry']['coordinates']
        return Coordinates(lat=x, lon=y, zoom=zoom)

    return


def parse_directions_result(response):
    assert response.status_code == 200
    data = response.json()
    return round(data['routes'][0]['distance'] / 1000, 1)
