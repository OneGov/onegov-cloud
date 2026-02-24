from __future__ import annotations

import requests
from purl import URL


from typing import overload, ClassVar, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from onegov.gis.models.coordinates import AnyCoordinates, RealCoordinates


Endpoint = Literal['directions', 'geocoding']
GeocodeProfile = Literal['places']
DirectionsProfile = Literal[
    'driving-traffic',
    'driving',
    'walking',
    'cycling'
]


class MapboxRequests:

    host: ClassVar[str] = 'https://api.mapbox.com'
    endpoints: ClassVar[tuple[Endpoint, ...]] = ('directions', 'geocoding')
    geocode_profiles: ClassVar[tuple[GeocodeProfile, ...]] = ('places', )
    directions_profiles: ClassVar[tuple[DirectionsProfile, ...]] = (
        'driving-traffic',
        'driving',
        'walking',
        'cycling'
    )

    @overload
    def __init__(
        self,
        access_token: str | None,
        endpoint: Literal['geocoding'] = 'geocoding',
        profile: GeocodeProfile = 'places',
        api_version: str = 'v5'
    ): ...

    @overload
    def __init__(
        self,
        access_token: str | None,
        endpoint: Literal['directions'],
        profile: DirectionsProfile,
        api_version: str = 'v5'
    ): ...

    def __init__(
        self,
        # NOTE: This is technically not optional, but for testing purposes
        #       we allow it to be optional
        access_token: str | None,
        endpoint: Endpoint = 'geocoding',
        profile: str = 'places',
        api_version: str = 'v5'
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
    def base_url(self) -> URL:
        url = URL(
            f'{self.host}/{self.endpoint}/{self.api_version}/{self.profile}')
        if self.access_token is not None:
            url = url.query_param('access_token', self.access_token)
        return url

    @overload
    def geocode(
        self,
        text: str | None = None,
        street: str | None = None,
        zip_code: str | None = None,
        city: str | None = None,
        # FIXME: Why is this abbreviated...
        ctry: str | None = None,
        locale: str | None = None,
        as_url: Literal[False] = False
    ) -> requests.Response: ...

    @overload
    def geocode(
        self,
        text: str | None = None,
        street: str | None = None,
        zip_code: str | None = None,
        city: str | None = None,
        # FIXME: Why is this abbreviated...
        ctry: str | None = None,
        locale: str | None = None,
        *,
        as_url: Literal[True]
    ) -> URL: ...

    @overload
    def geocode(
        self,
        text: str | None = None,
        street: str | None = None,
        zip_code: str | None = None,
        city: str | None = None,
        # FIXME: Why is this abbreviated...
        ctry: str | None = None,
        locale: str | None = None,
        *,
        as_url: bool
    ) -> requests.Response | URL: ...

    def geocode(
        self,
        text: str | None = None,
        street: str | None = None,
        zip_code: str | None = None,
        city: str | None = None,
        # FIXME: Why is this abbreviated...
        ctry: str | None = None,
        locale: str | None = None,
        as_url: bool = False
    ) -> requests.Response | URL:

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
        return requests.get(url.as_string(), timeout=60)

    @overload
    def directions(
        self,
        coordinates: Iterable[tuple[str | float, str | float]],
        as_url: Literal[False] = False
    ) -> requests.Response: ...

    @overload
    def directions(
        self,
        coordinates: Iterable[tuple[str | float, str | float]],
        as_url: Literal[True]
    ) -> URL: ...

    @overload
    def directions(
        self,
        coordinates: Iterable[tuple[str | float, str | float]],
        as_url: bool
    ) -> requests.Response | URL: ...

    def directions(
        self,
        coordinates: Iterable[tuple[str | float, str | float]],
        as_url: bool = False
    ) -> requests.Response | URL:
        """
        coordinates: iterable of tuples of (lat, lon)
        """
        url = self.base_url.add_path_segment(
            ';'.join(f'{c[1]},{c[0]}' for c in coordinates)
        )
        if as_url:
            return url
        return requests.get(url.as_string(), timeout=60)


def outside_bbox(
    coordinate: AnyCoordinates | None,
    bbox: Collection[RealCoordinates] | None
) -> bool:
    """Checks if the Coordinates instance is inside the bounding box defined
    by the most outward sitting points in an iterable of two+ Coordinates.
    """
    if not coordinate or not bbox:
        return False

    assert len(bbox) >= 2
    max_lat = max(c.lat for c in bbox)
    min_lat = min(c.lat for c in bbox)
    max_lon = max(c.lon for c in bbox)
    min_lon = min(c.lon for c in bbox)
    return not (
        (max_lat >= coordinate.lat >= min_lat)
        and (max_lon >= coordinate.lon >= min_lon)
    )
