from __future__ import annotations

import json
from babel import Locale
from requests.exceptions import JSONDecodeError

from onegov.user import UserGroup, UserGroupCollection
from onegov.translator_directory.constants import ASSIGNMENT_LOCATIONS
from onegov.gis import Coordinates
from onegov.gis.utils import MapboxRequests, outside_bbox
from onegov.translator_directory import log
from onegov.translator_directory import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import requests
    from wtforms.fields.choices import _Choice
    from collections.abc import Collection
    from onegov.gis.models.coordinates import AnyCoordinates, RealCoordinates
    from onegov.org.request import OrgRequest
    from onegov.translator_directory.request import TranslatorAppRequest
    from onegov.translator_directory.models.translator import Translator


def to_tuple(coordinate: RealCoordinates) -> tuple[float, float]:
    return coordinate.lat, coordinate.lon


def found_route(response: requests.Response) -> bool:
    try:
        found = response.status_code == 200 and response.json()['code'] == 'Ok'
        if not found:
            log.warning(json.dumps(response.json(), indent=2))
    except JSONDecodeError as exc:
        log.warning(f'Response did not contain valid JSON: {exc}')
        return False
    return found


def out_of_tolerance(
    old_distance: float | None,
    new_distance: float | None,
    tolerance_factor: float,
    max_tolerance: float | None = None
) -> bool:
    """Checks if distances are off by +- a factor, but returns False if a
    set max_tolerance is not exceeded. """

    if not old_distance or not new_distance:
        return False

    too_big = new_distance > old_distance + old_distance * tolerance_factor
    too_sml = new_distance < old_distance - old_distance * tolerance_factor
    exceed_max = (
        abs(new_distance - old_distance) > max_tolerance
        if max_tolerance is not None else False
    )

    if exceed_max:
        return True
    elif too_big or too_sml:
        return False

    return too_big or too_sml


def validate_geocode_result(
    response: requests.Response,
    zip_code: str | int | None,
    zoom: int | None = None,
    bbox: Collection[RealCoordinates] | None = None
) -> RealCoordinates | None:

    if response.status_code != 200:
        return None

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
        # NOTE: outside_bbox check guarantees we return RealCoordinates
        if outside_bbox(coordinates, bbox=bbox):
            continue
        return coordinates
    return None


def parse_directions_result(response: requests.Response) -> float:
    assert response.status_code == 200
    data = response.json()
    km = round(data['routes'][0]['distance'] / 1000, 1)
    return km


def same_coords(this: Coordinates, other: Coordinates) -> bool:
    return this.lat == other.lat and this.lon == other.lon


def update_drive_distances(
    request: TranslatorAppRequest,
    only_empty: bool,
    tolerance_factor: float = 0.1,
    max_tolerance: float | None = None,
    max_distance: float | None = None
) -> (tuple[int, int, int, list[Translator],
      list[tuple[Translator, float]]]):
    """
    Handles updating Translator.driving_distance. Can be used in a cli or view.

    """
    from onegov.translator_directory.models.translator import Translator

    assert request.app.coordinates, 'Requires home coordinates to be set'

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
                trs.drive_distance, dist, tolerance_factor, max_tolerance
            ) or (max_distance and dist > max_distance):
                tol_failed.append((trs, dist))
            else:
                trs.drive_distance = dist
                distance_changed += 1
        else:
            no_routes.append(trs)
    return total, routes_found, distance_changed, no_routes, tol_failed


def calculate_distance_to_location(
    request: TranslatorAppRequest,
    translator_coordinates: AnyCoordinates,
    location_key: str,
    custom_address: str | None = None,
) -> float | None:

    if not translator_coordinates:
        return None

    if custom_address:
        address = custom_address
    elif location_key in ASSIGNMENT_LOCATIONS:
        _, address = ASSIGNMENT_LOCATIONS[location_key]
    else:
        return None

    geocoding_api = MapboxRequests(
        request.app.mapbox_token,
        endpoint='geocoding'
    )

    try:
        geocode_response = geocoding_api.geocode(
            text=address,
            ctry='Schweiz'
        )

        if geocode_response.status_code != 200:
            return None

        data = geocode_response.json()
        if not data.get('features'):
            return None

        # Get coordinates of the assignment location
        location_coords = data['features'][0]['geometry']['coordinates']

        # Calculate driving distance
        directions_api = MapboxRequests(
            request.app.mapbox_token,
            endpoint='directions',
            profile='driving'
        )

        response = directions_api.directions([
            to_tuple(translator_coordinates),
            # lat, lon (GeoJSON returns [lon, lat])
            (location_coords[1], location_coords[0])
        ])

        if found_route(response):
            return parse_directions_result(response)

        return None

    except Exception:
        # Log error in production; for now return None
        return None


def geocode_translator_addresses(
    request: TranslatorAppRequest,
    only_empty: bool,
    bbox: Collection[RealCoordinates] | None = None
) -> tuple[int, int, int, int, list[Translator]]:
    from onegov.translator_directory.models.translator import Translator

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


def nationality_choices(locale: str | None) -> list[_Choice]:
    assert locale

    country_names = country_code_to_name(locale)
    pinned = ('CH', 'DE', 'FR', 'IT', 'AT', 'LI')
    nationalities: list[_Choice]
    nationalities = [(code, name) for code, name in
                     country_names.items() if code not in pinned]
    # pin common countries on top of the list
    nationalities.insert(0, ('', '------'))  # add divider
    for code in reversed(pinned):
        nationalities.insert(0, (code, country_names.get(code, code)))
    nationalities.insert(0, ('', ''))  # add empty choices

    return nationalities


def country_code_to_name(locale: str | None) -> dict[str, str]:
    """
    Returns a dict of country codes mapped to its country names according
    the given locale.

    Example:
        {'CH': 'Switzerland', 'DE': 'Germany, ...}

    """
    assert locale
    _locale = Locale.parse(locale)
    assert _locale
    mapping = {str(code): str(_locale.territories.get(code)) for code in
               _locale.territories if len(str(code)) == 2}

    return mapping


def get_custom_text(request: OrgRequest, key: str) -> str:
    """ Returns a custom text from the app's custom_texts dict. """
    custom_texts = request.app.custom_texts

    if not custom_texts:
        return _('Error: No custom texts found')

    return custom_texts.get(
        key, _(f"Error: No custom text found for '{key}'"))


def get_accountant_emails_for_finanzstelle(
    request: TranslatorAppRequest, finanzstelle_key: str | None
) -> set[str]:
    if not finanzstelle_key:
        raise ValueError(_('No Finanzstelle specified'))

    groups = (
        request.session.query(UserGroup)
        .filter(UserGroup.meta['finanzstelle'].astext == finanzstelle_key)
        .all()
    )

    emails = set()
    for group in groups:
        emails.update(group.meta.get('accountant_emails', []))

    if not emails:
        raise ValueError(
            request.translate(
                _(
                    'No accountant emails configured for Finanzstelle '
                    '"${fs}". Please configure user groups: ${url}',
                    mapping={
                        'fs': finanzstelle_key,
                        'url': request.class_link(UserGroupCollection),
                    },
                )
            )
        )

    return emails
