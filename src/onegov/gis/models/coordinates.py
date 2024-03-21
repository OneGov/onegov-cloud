from onegov.core.custom import json


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.schema import Column


class Coordinates(json.Serializable, keys=('lon', 'lat', 'zoom')):
    """ Represents a pair of coordinates.

    May contain zoom factor and other information like marker icon and
    color. Note that only latitude and longitude really matter, the rest
    may or may not be used.

    """

    __slots__ = ('lon', 'lat', 'zoom')

    def __init__(
        self,
        # FIXME: lat/lon being optional is seriously annoying for type
        #        safety, it should just be None or {} if it's unset.
        lat: float | None = None,
        lon: float | None = None,
        zoom: int | None = None
    ):
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


class CoordinatesMixin:
    """ Extends any class that has a content dictionary field with a single
    coordinates pair.

    """

    if TYPE_CHECKING:
        # forward declare content column from ContentMixin
        content: Column[dict[str, Any]]

    @property
    def coordinates(self) -> Coordinates:
        return self.content.get('coordinates') or Coordinates()

    @coordinates.setter
    def coordinates(self, value: Coordinates) -> None:
        self.content = self.content or {}
        self.content['coordinates'] = value or {}
