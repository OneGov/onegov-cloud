from __future__ import annotations

from onegov.api.models import ApiEndpoint, ApiEndpointItem
from onegov.event.collections import OccurrenceCollection
from onegov.gis import Coordinates


from typing import Any
from typing import TYPE_CHECKING

from onegov.org.models.page import News, NewsCollection, Topic, TopicCollection

if TYPE_CHECKING:
    from onegov.town6.app import TownApp
    from onegov.town6.request import TownRequest
    from onegov.event.models import Occurrence
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin
    from typing import TypeVar

    T = TypeVar('T')


def get_geo_location(item: ContentMixin) -> dict[str, Any]:
    geo = item.content.get('coordinates', Coordinates()) or Coordinates()
    return {'lon': geo.lon, 'lat': geo.lat, 'zoom': geo.zoom}


def get_modified_iso_format(item: TimestampMixin) -> str:
    """
    Returns the iso format of the modified or created field of item.

    :param item: db item e.g. agency, people, membership
    :return: str iso representation of item last modification
    """
    return item.last_change.isoformat()


class EventApiEndpoint(ApiEndpoint['Occurrence']):
    app: TownApp
    endpoint = 'events'

    @property
    def collection(self) -> Any:
        result = OccurrenceCollection(
            self.session,
            page=self.page or 0,
            only_public=True
        )

        result.batch_size = self.batch_size
        return result

    def item_data(self, item: Occurrence) -> dict[str, Any]:
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

    def item_links(self, item: Occurrence) -> dict[str, Any]:
        return {
            'html': item,
            'image': item.event.image,
            'pfd': item.event.pdf
        }


class NewsApiEndpoint(ApiEndpoint[News]):
    app: TownApp
    endpoint = 'news'
    filters = set()

    @property
    def collection(self) -> Any:
        result = NewsCollection(
            self.request,
            page=self.page or 0,
        )
        result.batch_size = 25
        return result

    def item_data(self, item: News) -> dict[str, Any]:
        if item.publication_start:
            publication_start = item.publication_start.isoformat()
        else:
            publication_start = None

        if item.publication_end:
            publication_end = item.publication_end.isoformat()
        else:
            publication_end = None

        return {
            'title': item.title,
            'lead': item.lead,
            'text': item.text,
            'hashtags': item.hashtags,
            'publication_start': publication_start,
            'publication_end': publication_end,
            'created': item.created.isoformat(),
            'modified': get_modified_iso_format(item),
        }

    def item_links(self, item: News) -> dict[str, Any]:
        return {
            'html': item,
            'image': item.page_image or None,
        }


class TopicApiEndpoint(ApiEndpoint[Topic]):
    request: TownRequest
    app: TownApp
    endpoint = 'topics'
    filters = set()

    @property
    def collection(self) -> Any:
        result = TopicCollection(
            self.session,
            page=self.page or 0,
            only_public=True
        )
        result.batch_size = 25
        return result

    def item_data(self, item: Topic) -> dict[str, Any]:
        if item.publication_start:
            publication_start = item.publication_start.isoformat()
        else:
            publication_start = None

        if item.publication_end:
            publication_end = item.publication_end.isoformat()
        else:
            publication_end = None

        return {
            'title': item.title,
            'lead': item.lead,
            'text': item.text,
            'publication_start': publication_start,
            'publication_end': publication_end,
            'created': item.created.isoformat(),
            'modified': get_modified_iso_format(item),
        }

    def item_links(self, item: Topic) -> dict[str, Any]:
        return {
            'html': item,
            'image': item.page_image or None,
            'parent': ApiEndpointItem(
                self.request, self.endpoint, str(item.parent_id)
            ) if item.parent_id is not None else None,
        }
