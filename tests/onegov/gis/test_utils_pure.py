from __future__ import annotations

from onegov.gis.utils import MapboxRequests, outside_bbox


def test_geocode_as_url_from_parts() -> None:
    request = MapboxRequests('token')
    url = request.geocode(
        street='Street 1', zip_code='6000', city='City',
        locale='de_CH', as_url=True)
    string = url.as_string()

    assert '.json' in string
    assert 'types=address' in string
    # the _CH suffix is stripped from the language parameter
    assert 'language=de' in string
    assert 'access_token=token' in string


def test_geocode_as_url_with_text() -> None:
    request = MapboxRequests('token')
    url = request.geocode(text='Bern', as_url=True)
    assert '.json' in url.as_string()


def test_directions_as_url() -> None:
    request = MapboxRequests('token', endpoint='directions', profile='driving')
    url = request.directions([(47.0, 8.0), (47.1, 8.1)], as_url=True)
    string = url.as_string()
    # coordinates are serialised as lon,lat
    assert '47.0' in string
    assert '8.1' in string


def test_outside_bbox_no_args() -> None:
    assert outside_bbox(None, None) is False
