from __future__ import annotations

from onegov.gis import Coordinates
from onegov.translator_directory.utils import (
    country_code_to_name,
    found_route,
    nationality_choices,
    out_of_tolerance,
    parse_directions_result,
    same_coords,
    to_tuple,
    validate_geocode_result,
)
from types import SimpleNamespace


from typing import Any


def _response(status: int = 200, payload: Any = None) -> Any:
    return SimpleNamespace(status_code=status, json=lambda: payload)


def test_to_tuple() -> None:
    assert to_tuple(Coordinates(lat=47.0, lon=8.0)) == (47.0, 8.0)


def test_same_coords() -> None:
    assert same_coords(
        Coordinates(lat=47.0, lon=8.0), Coordinates(lat=47.0, lon=8.0))
    assert not same_coords(
        Coordinates(lat=47.0, lon=8.0), Coordinates(lat=47.0, lon=9.0))


def test_found_route() -> None:
    assert found_route(_response(200, {'code': 'Ok'})) is True
    assert found_route(_response(200, {'code': 'NoRoute'})) is False
    assert found_route(_response(404, {'code': 'Ok'})) is False


def test_out_of_tolerance() -> None:
    # missing distances -> not out of tolerance
    assert out_of_tolerance(None, 100, 0.1) is False
    assert out_of_tolerance(100, None, 0.1) is False

    # within max tolerance -> False
    assert out_of_tolerance(100, 110, 0.1, max_tolerance=50) is False

    # exceeding the max tolerance -> True
    assert out_of_tolerance(100, 200, 0.1, max_tolerance=50) is True


def test_parse_directions_result() -> None:
    response = _response(200, {'routes': [{'distance': 5500}]})
    assert parse_directions_result(response) == 5.5


def test_validate_geocode_result() -> None:
    feature = {
        'matching_place_name': 'Street 1, 6000 City',
        'place_type': ['address'],
        'geometry': {'coordinates': [8.0, 47.0]},
    }
    response = _response(200, {'features': [feature]})

    result = validate_geocode_result(response, zip_code='6000')
    assert result is not None
    assert result.lat == 47.0
    assert result.lon == 8.0

    # non-200 -> None
    assert validate_geocode_result(_response(500, {}), zip_code='6000') is None

    # zip mismatch -> None
    assert validate_geocode_result(response, zip_code='9999') is None

    # no address place type -> None
    non_address = _response(200, {'features': [{
        'matching_place_name': 'x', 'place_type': ['poi'],
        'geometry': {'coordinates': [8.0, 47.0]},
    }]})
    assert validate_geocode_result(non_address, zip_code=None) is None


def test_country_code_to_name() -> None:
    mapping = country_code_to_name('de')
    assert mapping['CH'] == 'Schweiz'
    assert 'DE' in mapping
    # only two-letter codes
    assert all(len(code) == 2 for code in mapping)


def test_nationality_choices() -> None:
    choices = nationality_choices('de')
    values = [c.value for c in choices]
    # first entry is an empty choice, pinned countries come next
    assert values[0] == ''
    assert 'CH' in values
    assert 'DE' in values
