from __future__ import annotations

from datetime import date
from functools import cached_property
from onegov.api.models import ApiEndpoint, ApiEndpointItem
from onegov.api.models import ApiInvalidParamException
from onegov.core.converters import extended_date_decode
from onegov.event.collections import OccurrenceCollection
from onegov.gis import Coordinates
from onegov.org.models.directory import (
    ExtendedDirectory, ExtendedDirectoryEntry,
    ExtendedDirectoryEntryCollection)
from onegov.org.models.page import News, NewsCollection, Topic, TopicCollection
from onegov.town6 import _
from sqlalchemy.exc import SQLAlchemyError


from typing import Any, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from onegov.town6.app import TownApp
    from onegov.town6.request import TownRequest
    from onegov.event.models import Occurrence
    from onegov.core.collection import PKType
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin


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


def format_multiple_choice_prompt(
    choices: Collection[str] | None
) -> str | None:
    if not choices:
        return None
    if len(choices) == 1:
        choice, = choices
        return f'Either {choice!r} or left unspecified'
    formatted_choices = ', '.join(f'{choice!r}' for choice in choices)
    return f'One of {formatted_choices} (Can be specified multiple times)'


class EventApiEndpoint(ApiEndpoint['Occurrence']):
    app: TownApp
    endpoint = 'events'

    @cached_property
    def filters(self) -> Mapping[str, str | None]:
        collection = self._base_collection
        filters = {
            'start': 'Earliest event date '
                '(ISO-8601 encoded date: YYYY-MM-DD, defaults to today)',
            'end': 'Latest event date (ISO-8601 encoded date: YYYY-MM-DD)',
            'locations': 'Can be specified multiple times',
            'sources': format_multiple_choice_prompt(collection.used_sources)
        }

        filter_type = self.app.org.event_filter_type
        if filter_type in ('tags', 'tags_and_filters'):
            filters['tags'] = format_multiple_choice_prompt(
                collection.used_tags)

        for name, __, choices in collection.available_filters():
            filters[name] = format_multiple_choice_prompt(choices)
        return filters

    @property
    def title(self) -> str:
        return self.request.translate(_('Events'))

    @property
    def description(self) -> str | None:
        return self.app.org.event_header_html or self.app.org.event_footer_html

    # NOTE: Since we need the collection in order to determine which
    #       filters are available we cannot call `assert_valid_filter`
    #       in the same property that gets accessed by filters. So we
    #       split creating the collection into two steps, since the first
    #       step is sufficient for determining the filters.
    @cached_property
    def _base_collection(self) -> OccurrenceCollection:
        result = OccurrenceCollection(
            self.session,
            page=self.page or 0,
            only_public=True
        )

        filter_type = self.app.org.event_filter_type
        filter_config = self.app.org.event_filter_configuration
        if (
            filter_type in ('filters', 'tags_and_filters')
            and filter_config.get('keywords', None)
        ):
            result.set_event_filter_configuration(filter_config)
            result.set_event_filter_fields(self.app.org.event_filter_fields)
        return result

    def get_date_filter(self, key: str, values: list[str]) -> date | None:
        value = self.scalarize_value(key, values)
        if value is None:
            return None
        try:
            return extended_date_decode(value)
        except Exception:
            raise ApiInvalidParamException(
                f'Invalid ISO-8601 date for parameter {key!r}'
            ) from None

    @property
    def collection(self) -> OccurrenceCollection:
        result = self._base_collection
        filter_keywords = {}
        for key, values in self.extra_parameters.items():
            self.assert_valid_filter(key)
            if key == 'start':
                value = self.get_date_filter(key, values)
                result = result.for_filter(
                    start=value,
                    outdated=value < date.today() if value else False,
                )
            elif key == 'end':
                value = self.get_date_filter(key, values)
                result = result.for_filter(end=value)
            elif key == 'tags':
                result = result.for_filter(tags=values)
            elif key == 'sources':
                result = result.for_filter(sources=values)
            elif key == 'locations':
                result = result.for_filter(locations=values)
            else:
                filter_keywords[key] = values

        if filter_keywords:
            result = result.for_keywords(**filter_keywords)

        result.batch_size = self.batch_size
        return result

    def item_data(self, item: Occurrence) -> dict[str, Any]:
        data: dict[str, Any] = {
            'title': item.title,
            'description': item.event.description,
            'organizer': item.event.organizer,
            'organizer_email': item.event.organizer_email,
            'organizer_phone': item.event.organizer_phone,
            'external_event_url': item.event.external_event_url,
            'event_registration_url': item.event.event_registration_url,
            'price': item.event.price,
            'start': item.start.isoformat(),
            'end': item.end.isoformat(),
            'location': item.location,
            'source': item.event.source,
            'coordinates': get_geo_location(item),
        }

        filter_type = self.app.org.event_filter_type
        if filter_type in ('tags', 'tags_and_filters'):
            data['tags'] = item.event.tags

        if filter_type in ('filters', 'tags_and_filters'):
            data.update(item.event.filter_keywords)

        data['created'] = item.created.isoformat()
        data['modified'] = get_modified_iso_format(item)
        return data

    def item_links(self, item: Occurrence) -> dict[str, Any]:
        return {
            'html': item,
            'image': item.event.image,
            'pdf': item.event.pdf
        }


class NewsApiEndpoint(ApiEndpoint[News]):
    app: TownApp
    endpoint = 'news'

    @property
    def title(self) -> str:
        return self.request.translate(_('Latest news'))

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

    @property
    def title(self) -> str:
        return self.request.translate(_('Topics'))

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


class DirectoryEntryApiEndpoint(ApiEndpoint[ExtendedDirectoryEntry]):
    request: TownRequest
    app: TownApp
    endpoint: str

    def __init__(
        self,
        request: TownRequest,
        name: str,
        extra_parameters: dict[str, list[str]] | None = None,
        page: int | None = None,
    ):
        super().__init__(request, extra_parameters, page)
        self.endpoint = name

    @property
    def title(self) -> str:
        return self.directory.title

    @property
    def description(self) -> str | None:
        return self.directory.lead

    @cached_property
    def directory(self) -> ExtendedDirectory:
        return self.request.session.query(ExtendedDirectory).filter_by(
            name=self.endpoint
        ).one()

    @property
    def collection(self) -> Any:
        result = ExtendedDirectoryEntryCollection(
            self.directory,
            request=self.request,
            page=self.page or 0,
            published_only=True
        )
        result.batch_size = 25
        return result

    def for_page(self, page: int | None) -> DirectoryEntryApiEndpoint:
        """ Return a new endpoint instance with the given page while keeping
        the current filters.

        """

        return self.__class__(self.request, self.endpoint,
                              self.extra_parameters, page)

    def for_filter(self, **filters: Any) -> Self:
        """ Return a new endpoint instance with the given filters while
        discarding the current filters and page.

        """

        return self.__class__(self.request, self.endpoint, filters)

    def by_id(
            self, id: PKType
              ) -> ExtendedDirectoryEntry | None:
        """ Return the item with the given ID from the collection. """

        try:
            return self.collection.by_id(id)
        except SQLAlchemyError:
            return None

    def item_data(self, item: ExtendedDirectoryEntry) -> dict[str, Any]:
        data: dict[str, Any] = {}
        data['title'] = item.title
        data['lead'] = item.lead

        if item.access == 'public':
            if item.content_fields:
                data = {f.name: f.object_data for f in item.content_fields}

            for field in item.directory.fields:
                if any(field_type in field.type for field_type in [
                    'fileinput', 'url']):
                    data.pop(field.id, None)
                if any(field_type in field.type for field_type in [
                    'date', 'time']):
                    if data.get(field.id):
                        data[field.id] = data[field.id].isoformat()
                if 'decimal_range' in field.type:
                    if data.get(field.id) is not None:
                        data[field.id] = float(data[field.id])

            data['coordinates'] = get_geo_location(item)
            data['contact'] = item.contact

        return data

    def item_links(self, item: ExtendedDirectoryEntry) -> dict[str, Any]:
        data = {}
        if item.access == 'public':
            content_field_names = []
            if item.content_fields:
                content_field_names = [i.name for i in item.content_fields]
            data = {
                (file.note or 'file'): file
                for file in item.files
                if file.note
                if file.note.split(':', 1)[0] in content_field_names
            }
            for field in item.content_fields or []:
                if field.type == 'URLField':
                    data[field.name] = field.data
        data['html'] = item  # type: ignore

        return data
