from onegov.gis import Coordinates
from onegov.gis.utils import MapboxRequests
from onegov.translator_directory.models.translator import Translator


def to_tuple(coordinate):
    return coordinate.lat, coordinate.lon


def found_route(response):
    return response.status_code == 200 and response.json()['code'] == 'Ok'


def out_of_tolerance(old_distance, new_distance, tolerance_factor):
    if not old_distance or not new_distance:
        return False
    too_big = new_distance > old_distance + old_distance * tolerance_factor
    too_sml = new_distance < old_distance - old_distance * tolerance_factor
    return too_big or too_sml


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


def update_distances(request, only_empty, tolerance_factor):
    no_routes = []
    tol_failed = []
    distance_changed = 0
    routes_found = 0
    total = 0

    directions_api = MapboxRequests(
        request.app.mapbox_token,
        endpoint='directions',
        profile='driving'
    )
    query = request.session.query(Translator)
    if only_empty:
        query = query.filter(Translator.drive_distance == None)

    for trs in query:
        if not trs.coordinates:
            continue
        total += 1
        response = directions_api.directions([
            to_tuple(request.app.coordinates),
            to_tuple(trs.coordinates)
        ])
        if found_route(response):
            routes_found += 1
            dist = parse_directions_result(response)
            if not out_of_tolerance(
                    trs.drive_distance, dist, tolerance_factor):
                trs.drive_distance = dist
                distance_changed += 1
            else:
                tol_failed.append(trs)
        else:
            no_routes.append(trs)
        return total, routes_found, distance_changed, no_routes, tol_failed
