from functools import cached_property
from onegov.event.collections import OccurrenceCollection
from onegov.api import ApiEndpoint
from onegov.gis import Coordinates


from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.town6.app import TownApp
    from onegov.event.models import Occurrence
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin
    from typing import TypeVar

    T = TypeVar('T')


class ApisMixin:

    app: 'TownApp'

    @cached_property
    def event_api(self) -> 'EventApiEndpoint':
        return EventApiEndpoint(self.app)


def get_geo_location(item: 'ContentMixin') -> dict[str, Any]:
    geo = item.content.get('coordinates', Coordinates()) or Coordinates()
    return {'lon': geo.lon, 'lat': geo.lat, 'zoom': geo.zoom}


def get_modified_iso_format(item: 'TimestampMixin') -> str:
    """
    Returns the iso format of the modified or created field of item.

    :param item: db item e.g. agency, people, membership
    :return: str iso representation of item last modification
    """
    return item.last_change.isoformat()


class EventApiEndpoint(
    ApiEndpoint['Occurrence'],
    ApisMixin
):
    app: 'TownApp'
    endpoint = 'events'
    filters = {
            'range', 'start', 'end', 'outdated', 'tags', 'locations',
            'only_public', 'search_widget', 'event_filter_configuration',
            'event_filter_fields'
    }

    @property
    def collection(self) -> Any:
        result = OccurrenceCollection(
            self.session,
            page=self.page or 0
        )

        result.batch_size = self.batch_size
        return result

    def item_data(self, item: 'Occurrence') -> dict[str, Any]:
        return {
            'title': item.title,
            'description': item.event.description,
            'organizer': item.event.organizer,
            'organizer_email': item.event.organizer_email,
            'organizer_phone': item.event.organizer_phone,
            'external_event_url': item.event.external_event_url,
            'event_registration_url': item.event.event_registration_url,
            'price': item.event.price,
            'tags': item.event.tags,
            'start': item.start.isoformat(),
            'end': item.end.isoformat(),
            'location': item.location,
            'coordinates': get_geo_location(item),
            'created': item.created.isoformat(),
            'modified': get_modified_iso_format(item),
        }

    def item_links(self, item: 'Occurrence') -> dict[str, Any]:
        return {
            'image': item.event.image,
            'pfd': item.event.pdf
        }
