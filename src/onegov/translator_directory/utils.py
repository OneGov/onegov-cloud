import json

from onegov.gis import Coordinates
from onegov.gis.utils import MapboxRequests, outside_bbox
from onegov.translator_directory import log
from onegov.translator_directory.models.translator import Translator


def to_tuple(coordinate):
    return coordinate.lat, coordinate.lon


def found_route(response):
    found = response.status_code == 200 and response.json()['code'] == 'Ok'
    if not found:
        log.warning(json.dumps(response.json(), indent=2))
    return found


def out_of_tolerance(old_distance, new_distance, tolerance_factor,
                     max_tolerance=None):
    """Checks if distances are off by +- a factor, but returns False if a
    set max_tolerance is not exceeded. """

    if not old_distance or not new_distance:
        return False

    too_big = new_distance > old_distance + old_distance * tolerance_factor
    too_sml = new_distance < old_distance - old_distance * tolerance_factor
    exceed_max = abs(new_distance - old_distance) > max_tolerance \
        if max_tolerance is not None else False

    if exceed_max:
        return True
    elif too_big or too_sml:
        return False

    return too_big or too_sml


def validate_geocode_result(response, zip_code, zoom=None, bbox=None):

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
        coordinates = Coordinates(lat=x, lon=y, zoom=zoom)
        if outside_bbox(coordinates, bbox=bbox):
            continue
        return coordinates
    return


def parse_directions_result(response):
    assert response.status_code == 200
    data = response.json()
    km = round(data['routes'][0]['distance'] / 1000, 1)
    return km


def same_coords(this, other):
    return this.lat == other.lat and this.lon == other.lon


def update_drive_distances(
        request,
        only_empty,
        tolerance_factor=0.1,
        max_tolerance=None,
        max_distance=None
):
    """
    Handles updating Translator.driving_distance. Can be used in a cli or view.

    """
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
            if out_of_tolerance(
                    trs.drive_distance, dist, tolerance_factor, max_tolerance):
                tol_failed.append((trs, dist))
            elif max_distance and dist > max_distance:
                tol_failed.append((trs, dist))
            else:
                trs.drive_distance = dist
                distance_changed += 1
        else:
            no_routes.append(trs)
    return total, routes_found, distance_changed, no_routes, tol_failed


def geocode_translator_addresses(request, only_empty, bbox=None):

    api = MapboxRequests(request.app.mapbox_token)
    total = 0
    geocoded = 0
    skipped = 0
    coords_not_found = []

    trs_total = request.session.query(Translator).count()

    for trs in request.session.query(Translator).filter(
        Translator.city != None,
        Translator.address != None,
        Translator.zip_code != None
    ):
        total += 1

        if only_empty and trs.coordinates:
            skipped += 1
            continue

        # Might still be empty
        if not all((trs.city, trs.address, trs.zip_code)):
            skipped += 1
            continue

        response = api.geocode(
            street=trs.address,
            zip_code=trs.zip_code,
            city=trs.city,
            ctry='Schweiz'
        )
        coordinates = validate_geocode_result(
            response,
            trs.zip_code,
            trs.coordinates.zoom,
            bbox
        )
        if coordinates:
            if same_coords(trs.coordinates, coordinates):
                continue
            trs.coordinates = coordinates
            request.session.flush()
            geocoded += 1
        else:
            coords_not_found.append(trs)

    return trs_total, total, geocoded, skipped, coords_not_found
