from __future__ import annotations

import pytest

from onegov.gis import Coordinates
from onegov.gis.utils import MapboxRequests, outside_bbox


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.gis.models.coordinates import AnyCoordinates


valid_address = 'Pilatusstrasse 3, 6003 Luzern, Schweiz'
luzern = (47.04575, 8.309)
luzern_2 = (47.05646, 8.29394)


def test_mapbox_requests() -> None:
    token = 'a_token'
    host = MapboxRequests.host
    api = MapboxRequests(token, endpoint='geocoding', profile='places')
    assert api.base_url.as_string() == (
           f'{host}/geocoding/v5/mapbox.places?access_token={token}'
    )

    geocode_url = api.geocode(valid_address, as_url=True).as_string()
    assert geocode_url == (
           f'{host}/geocoding/v5/mapbox.places/'
           f'Pilatusstrasse%203%2C%206003%20Luzern%2C%20Schweiz.json'
           f'?access_token={token}&types=address'
    )

    api = MapboxRequests(token, endpoint='directions', profile='driving')
    assert api.base_url.as_string() == (
           f'{host}/directions/v5/mapbox/driving?access_token={token}'
    )

    url = api.directions([luzern, luzern_2], as_url=True)
    assert url.as_string() == (
           f'{host}/directions/v5/mapbox/driving/{luzern[1]},{luzern[0]};'
           f'{luzern_2[1]},{luzern_2[0]}?access_token={token}'
    ).replace(',', '%2C').replace(';', '%3B')


@pytest.mark.parametrize('coord,outcome', [
    (Coordinates(lat=0.99, lon=1), True),
    (Coordinates(lat=1, lon=1), False),
    (Coordinates(lat=2, lon=2), False),
    (Coordinates(lat=1.5, lon=2.1), True),
    (Coordinates(lat=1.1, lon=1.9), False)
])
def test_outside_bbox(coord: AnyCoordinates, outcome: bool) -> None:
    bbox = [
        Coordinates(lat=1, lon=1),
        Coordinates(lat=2, lon=2),
        Coordinates(lat=1.5, lon=1.5)   # ignored by the implementation
    ]
    assert outside_bbox(coord, bbox) == outcome
