from __future__ import annotations

from onegov.core.custom import json


from typing import overload, Any, Literal, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.schema import Column
    from typing import TypeAlias

    AnyCoordinates: TypeAlias = 'RealCoordinates | NullCoordinates'


class Coordinates(json.Serializable, keys=('lon', 'lat', 'zoom')):
    """ Represents a pair of coordinates.

    May contain zoom factor and other information like marker icon and
    color. Note that only latitude and longitude really matter, the rest
    may or may not be used.

    """

    __slots__ = ('lon', 'lat', 'zoom')

    lat: float | None
    lon: float | None
    zoom: int | None

    if TYPE_CHECKING:
        @overload
        def __new__(
            cls,
            lat: float,
            lon: float,
            zoom: int | None = None,
        ) -> RealCoordinates: ...

        @overload
        def __new__(
            cls,
            lat: None = None,
            lon: None = None,
            zoom: None = None,
        ) -> NullCoordinates: ...

        def __new__(
            cls,
            lat: float | None = None,
            lon: float | None = None,
            zoom: int | None = None,
        ) -> Self:
            raise NotImplementedError()
    else:

        def __init__(
            self,
            lat: float | None = None,
            lon: float | None = None,
            zoom: int | None = None
        ) -> None:

            self.lat = lat
            self.lon = lon
            self.zoom = zoom

    def __bool__(self) -> bool:
        if self.lat is None or self.lon is None:
            return False
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Coordinates):
            return False

        return (
            self.lat == other.lat
            and self.lon == other.lon
            and self.zoom == other.zoom
        )


if TYPE_CHECKING:
    class NullCoordinates(Coordinates, keys=('lon', 'lat', 'zoom')):

        lat: None
        lon: None
        zoom: None

        def __bool__(self) -> Literal[False]:
            return False

    class RealCoordinates(Coordinates, keys=('lon', 'lat', 'zoom')):

        lat: float
        lon: float
        zoom: int | None

        def __bool__(self) -> Literal[True]:
            return True


class CoordinatesMixin:
    """ Extends any class that has a content dictionary field with a single
    coordinates pair.

    """

    if TYPE_CHECKING:
        # forward declare content column from ContentMixin
        content: Column[dict[str, Any]]

    @property
    def coordinates(self) -> AnyCoordinates:
        return self.content.get('coordinates') or Coordinates()

    @coordinates.setter
    def coordinates(self, value: AnyCoordinates) -> None:
        self.content = self.content or {}
        self.content['coordinates'] = value or {}
