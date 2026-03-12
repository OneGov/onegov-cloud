from __future__ import annotations

from json import dumps
from onegov.gis.utils import MapboxRequests
from onegov.translator_directory import _, log
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.utils import parse_directions_result


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.gis import CoordinatesField
    from onegov.gis.models.coordinates import RealCoordinates
    from onegov.translator_directory.request import TranslatorAppRequest
    from wtforms import FloatField


class DrivingDistanceMixin:

    request: TranslatorAppRequest

    if TYPE_CHECKING:
        # forward declare required fields
        coordinates: CoordinatesField
        drive_distance: FloatField

    @property
    def directions_api(self) -> MapboxRequests:
        return MapboxRequests(
            self.request.app.mapbox_token,
            endpoint='directions',
            profile='driving'
        )

    def ensure_updated_driving_distance(self) -> bool:
        if not self.coordinates.data:
            return True

        if (
            hasattr(self, 'model')
            and isinstance(self.model, Translator)
            and self.model.coordinates == self.coordinates.data
        ):
            return True

        def to_tuple(coordinate: RealCoordinates) -> tuple[float, float]:
            return coordinate.lat, coordinate.lon

        if not self.request.app.coordinates:
            assert isinstance(self.coordinates.errors, list)
            self.coordinates.errors.append(
                _('Home location is not configured. '
                  'Please complete location settings first')
            )
            return False

        response = self.directions_api.directions([
            to_tuple(self.request.app.coordinates),
            to_tuple(self.coordinates.data)
        ])

        if response.status_code == 422:
            message = response.json()['message']
            assert isinstance(self.coordinates.errors, list)
            self.coordinates.errors.append(message)
            log.warning(f'ensure_update_driving_distance: {message}')
            return False

        if response.status_code != 200:
            assert isinstance(self.coordinates.errors, list)
            self.coordinates.errors.append(
                _('Error in requesting directions from Mapbox (${status})',
                  mapping={'status': response.status_code})
            )
            log.warning(f'Failed to fetch directions '
                        f'status {response.status_code}, '
                        f'url: {response.url}')
            log.warning(dumps(response.json(), indent=2))
            return False

        data = response.json()

        if data['code'] == 'NoRoute':
            assert isinstance(self.coordinates.errors, list)
            self.coordinates.errors.append(
                _('Could not find a route. Check the address again')
            )
            return False

        if data['code'] == 'NoSegment':
            assert isinstance(self.coordinates.errors, list)
            self.coordinates.errors.append(
                _('Check if the location of the translator is near a road')
            )
            return False

        self.drive_distance.data = parse_directions_result(response)
        return True
