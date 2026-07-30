from __future__ import annotations

import transaction

from datetime import date
from functools import cached_property
from onegov.api.models import AdjacencyListApiEndpoint
from onegov.api.models import ApiEndpoint, ApiEndpointItem
from onegov.api.models import ApiInvalidParamException
from onegov.core.collection import Pagination
from onegov.core.converters import extended_date_decode
from onegov.event.collections import OccurrenceCollection
from onegov.form import FormCollection
from onegov.form.models import FormDefinition
from onegov.gis import Coordinates
from onegov.org import _
from onegov.org.models.directory import (
    ExtendedDirectory, ExtendedDirectoryEntry,
    ExtendedDirectoryEntryCollection)
from onegov.org.models.external_link import (
    ExternalFormLink, ExternalLinkCollection, ExternalResourceLink)
from onegov.org.models.page import News, NewsCollection, Topic, TopicCollection
from onegov.people import Person
from onegov.people.collections import PersonCollection
from onegov.reservation.collection import ResourceCollection
from onegov.reservation.models import Resource
from onegov.search import SearchIndex
from onegov.search.utils import language_from_locale
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID


from typing import Any, Protocol, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Mapping, Sequence
    from onegov.core.collection import PKType
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin
    from onegov.event.models import Occurrence
    from onegov.org.app import OrgApp
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import DeclarativeBase, Query

    class CollectionLike[T: DeclarativeBase, IdT: PKType](Protocol):
        def query(self) -> Query[T]: ...
        def by_id(self, id: IdT, /) -> T | None: ...


type FormOrExternalLink = FormDefinition | ExternalFormLink
type ResourceOrExternalLink = Resource | ExternalResourceLink


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


def apply_visibility_filters[T: DeclarativeBase](
    request: OrgRequest,
    query: Query[T],
    model_class: type[T],
) -> Query[T]:
    role = getattr(request.identity, 'role', 'anonymous')
    available_accesses = {
        'admin': (),  # can see everything
        'editor': (),  # can see everything
        'member': ('member', 'mtan', 'public')
    }.get(role, ('mtan', 'public'))
    if hasattr(model_class, 'meta') and available_accesses:
        query = query.filter(or_(
            *(
                model_class.meta['access'].astext == access  # type: ignore[attr-defined]
                for access in available_accesses
            ),
            model_class.meta['access'].is_(None)  # type: ignore[attr-defined]
        ))

    if (
        role not in ('admin', 'editor')
        and hasattr(model_class, 'publication_started')
        and hasattr(model_class, 'publication_ended')
    ):
        query = query.filter(
            model_class.publication_started == True,  # type: ignore[attr-defined]
            model_class.publication_ended == False  # type: ignore[attr-defined]
        )

    return query


class PaginatedCollection[T: DeclarativeBase, IdT: PKType](Pagination[T]):

    def __init__(
        self,
        request: OrgRequest,
        collection: CollectionLike[T, IdT],
        model_class: type[T],
        batch_size: int,
        page: int = 0,
    ) -> None:
        self.request = request
        self.collection = collection
        self.model_class = model_class
        self.page = page
        self.batch_size = batch_size

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.request is other.request
            and self.collection == other.collection
            and self.model_class is other.model_class
            and self.page == other.page
        )

    def by_id(self, id: IdT) -> T | None:
        result = self.collection.by_id(id)
        if result and self.request.is_visible(result):
            return result
        return None

    def subset(self) -> Query[T]:
        return apply_visibility_filters(
            self.request,
            self.collection.query(),
            self.model_class,
        )

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.request,
            self.collection,
            self.model_class,
            batch_size=self.batch_size,
            page=index,
        )

    @property
    def page_index(self) -> int:
        return self.page


class PaginatedSumCollection[T: DeclarativeBase, IdT: PKType](Pagination[T]):

    def __init__(
        self,
        request: OrgRequest,
        collections: Sequence[tuple[CollectionLike[T, IdT], type[T]]],
        batch_size: int,
        page: int = 0,
    ) -> None:
        self.request = request
        self.collections = tuple(collections)
        self.batch_size = batch_size
        self.page = page

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.request is other.request
            and self.collections == other.collections
            and self.page == other.page
        )

    def by_id(self, id: IdT) -> T | None:
        for collection, model_class in self.collections:
            savepoint = transaction.savepoint()
            try:
                result = collection.by_id(id)
            except SQLAlchemyError:
                # HACK: Allows mixed pk types to work
                savepoint.rollback()
                result = None

            if result is not None:
                break

        if result and self.request.is_visible(result):
            return result
        return None

    def subset(self) -> Query[T]:
        raise NotImplementedError(
            'PaginatedSumCollection does not expose a single subset query'
        )

    @cached_property
    def cached_subset(self) -> Query[T]:
        raise NotImplementedError(
            'PaginatedSumCollection does not expose a single cached subset'
        )

    @cached_property
    def counts(self) -> tuple[int, ...]:
        return tuple(
            apply_visibility_filters(
                self.request,
                collection.query().order_by(None),
                model_class,
            ).count()
            for collection, model_class in self.collections
        )

    @cached_property
    def subset_count(self) -> int:
        return sum(self.counts)

    @cached_property
    def batch(self) -> tuple[T, ...]:
        offset = self.offset
        remaining = self.batch_size
        items: list[T] = []

        for (
            collection,
            model_class,
        ), count in zip(self.collections, self.counts):
            if remaining <= 0:
                break
            if offset >= count:
                offset -= count
                continue

            query = apply_visibility_filters(
                self.request,
                collection.query(),
                model_class,
            ).offset(offset).limit(remaining)
            batch = tuple(query)
            items.extend(batch)
            remaining -= len(batch)
            offset = 0

        return tuple(items)

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.request,
            self.collections,
            page=index,
            batch_size=self.batch_size,
        )

    @property
    def page_index(self) -> int:
        return self.page


class EventApiEndpoint(ApiEndpoint['Occurrence', UUID]):
    app: OrgApp
    endpoint = 'events'
    pk_type = UUID

    @cached_property
    def filters(self) -> Mapping[str, Collection[str] | str | None]:
        collection = self._base_collection
        filters: dict[str, Collection[str] | str | None] = {
            'search': 'Performs a full-text search for the given term',
            'start': 'Earliest event date '
            '(ISO-8601 encoded date: YYYY-MM-DD, defaults to today)',
            'end': 'Latest event date (ISO-8601 encoded date: YYYY-MM-DD)',
            'locations': 'Can be specified multiple times',
            'sources': sorted(collection.used_sources),
            'syndicate': ('true', 'false'),
            'highlight': ('true', 'false'),
        }
        if not self.app.fts_search_enabled:
            del filters['search']

        filter_type = self.app.org.event_filter_type
        if filter_type in ('tags', 'tags_and_filters'):
            used_tags = collection.used_tags
            if not self.app.custom_event_tags:
                # built-in tags need to be translated
                used_tags = {
                    self.request.translate(_(tag))
                    for tag in used_tags
                }
            filters['tags'] = sorted(used_tags)

        filters.update(
            (name, choices)
            for name, __, choices in collection.available_filters()
        )
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
        role = getattr(self.request.identity, 'role', 'anonymous')
        available_accesses = {
            'admin': (),  # can see everything
            'editor': (),  # can see everything
            'member': ('member', 'mtan', 'public')
        }.get(role, ('mtan', 'public'))
        result = OccurrenceCollection(
            self.session,
            page=self.page or 0,
            available_accesses=available_accesses
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
            if key == 'search':
                term = self.scalarize_value(key, values)
                result = result.for_filter(term=term)
            elif key == 'start':
                value = self.get_date_filter(key, values)
                result = result.for_filter(
                    start=value,
                    outdated=value < date.today() if value else False,
                )
            elif key == 'end':
                value = self.get_date_filter(key, values)
                result = result.for_filter(end=value)
            elif key == 'tags':
                if not self.app.custom_event_tags:
                    # FIXME: circular import
                    from onegov.org.forms.event import TAGS
                    # built-in tags are translated and need to be
                    # transformed back to the stored tag name
                    translated_to_orginal = {
                        self.request.translate(tag): str(tag)
                        for tag in TAGS
                    }
                    values = [
                        translated_to_orginal.get(value, value)
                        for value in values
                    ]
                result = result.for_filter(tags=values)
            elif key == 'sources':
                result = result.for_filter(sources=values)
            elif key == 'locations':
                result = result.for_filter(locations=values)
            elif key == 'syndicate':
                syn = self.scalarize_value(key, values)
                if syn and syn.lower() == 'true':
                    result = result.for_filter(syndicate=True)
                elif syn and syn.lower() == 'false':
                    result = result.for_filter(
                        syndicate=False
                    )
            elif key == 'highlight':
                hl = self.scalarize_value(key, values)
                if hl and hl.lower() == 'true':
                    result = result.for_filter(highlight=True)
                elif hl and hl.lower() == 'false':
                    result = result.for_filter(highlight=False)
            else:
                filter_keywords[key] = values

        if filter_keywords:
            result = result.for_keywords(**filter_keywords)

        result.page = self.page or 0
        result.batch_size = self.batch_size
        return result

    def item_data(self, item: Occurrence) -> dict[str, Any]:
        source = item.event.source
        if source:
            # Only include the source prefix
            source = '-'.join(source.split('-', 2)[:2])
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
            'source': source,
            'coordinates': get_geo_location(item),
        }

        filter_type = self.app.org.event_filter_type
        if filter_type in ('tags', 'tags_and_filters'):
            tags = item.event.tags
            if not self.app.custom_event_tags:
                # built-in tags need to be translated
                tags = [self.request.translate(_(tag)) for tag in tags]
            data['tags'] = tags

        if filter_type in ('filters', 'tags_and_filters'):
            data.update(item.event.filter_keywords_ordered())

        data['syndicate'] = item.event.syndicate or False
        data['highlight'] = item.event.highlight or False
        data['created'] = item.created.isoformat()
        data['modified'] = get_modified_iso_format(item)
        return data

    def item_links(self, item: Occurrence) -> dict[str, Any]:
        return {
            'html': item,
            'image': item.event.image,
            'pdf': item.event.pdf
        }


# NOTE: News is a flat two-level tree (one shared root), so it's not an N+1
#       like topics/agencies -- hence plain ApiEndpoint here.
class NewsApiEndpoint(ApiEndpoint[News, int]):
    app: OrgApp
    request: OrgRequest
    endpoint = 'news'
    pk_type = int

    @cached_property
    def filters(self) -> Mapping[str, Collection[str] | str | None]:
        if self.app.fts_search_enabled:
            return {'search': 'Performs a full-text search for the given term'}
        return {}

    @property
    def title(self) -> str:
        return self.request.translate(_('Latest news'))

    @property
    def collection(self) -> Any:
        result = NewsCollection(
            self.request,
            page=self.page or 0,
        )
        for key, values in self.extra_parameters.items():
            self.assert_valid_filter(key)
            if key == 'search':
                result.term = self.scalarize_value(key, values)
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
        data = {
            'title': item.title,
            'lead': item.lead,
            'text': item.text,
            'hashtags': item.hashtags,
            'publication_start': publication_start,
            'publication_end': publication_end,
            'created': item.created.isoformat(),
            'modified': get_modified_iso_format(item),
        }
        if item.access == 'mtan' and not self.request.is_manager:
            # remove the part that should not be public
            del data['text']
        return data

    def item_links(self, item: News) -> dict[str, Any]:
        return {
            'html': item,
            'image': item.page_image or None,
        }


class TopicApiEndpoint(AdjacencyListApiEndpoint[Topic, int]):
    request: OrgRequest
    app: OrgApp
    endpoint = 'topics'
    pk_type = int

    @cached_property
    def filters(self) -> Mapping[str, Collection[str] | str | None]:
        if self.app.fts_search_enabled:
            return {'search': 'Performs a full-text search for the given term'}
        return {}

    @property
    def title(self) -> str:
        return self.request.translate(_('Topics'))

    @property
    def collection(self) -> Any:
        result = TopicCollection(
            self.request,
            page=self.page or 0
        )
        for key, values in self.extra_parameters.items():
            self.assert_valid_filter(key)
            if key == 'search':
                result.term = self.scalarize_value(key, values)
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

        data = {
            'title': item.title,
            'lead': item.lead,
            'text': item.text,
            'publication_start': publication_start,
            'publication_end': publication_end,
            'created': item.created.isoformat(),
            'modified': get_modified_iso_format(item),
        }
        if item.access == 'mtan' and not self.request.is_manager:
            # remove the part that should not be public
            del data['text']
        return data

    def item_links(self, item: Topic) -> dict[str, Any]:
        return {
            'html': item,
            'image': item.page_image or None,
            'parent': ApiEndpointItem(
                self.request, self.endpoint, str(item.parent_id)
            ) if item.parent_id is not None else None,
        }


# NOTE: The only thing we make use of is `adapt` to inject fulltext search
class DummyDirectorySearchWidget:
    name: str
    search_query: Query[ExtendedDirectoryEntry]

    def __init__(self, request: OrgRequest, term: str | None) -> None:
        self.request = request
        self.term = term

    def adapt[T](self, query: Query[T]) -> Query[T]:
        if self.term:
            language = self.request.locale
            if language_from_locale(language) == 'simple':
                language = 'simple'
            query = query.join(
                SearchIndex,
                and_(
                    SearchIndex.owner_id_uuid == ExtendedDirectoryEntry.id,
                    SearchIndex.owner_type == 'ExtendedDirectoryEntry'
                )
            )
            query = query.filter(SearchIndex.data_vector.op('@@')(
                func.websearch_to_tsquery(language, self.term)
            ))
        return query

    def html(self, layout: Any) -> Any:
        raise NotImplementedError()


class DirectoryEntryApiEndpoint(ApiEndpoint[ExtendedDirectoryEntry, UUID]):
    request: OrgRequest
    app: OrgApp
    endpoint: str
    pk_type = UUID

    @cached_property
    def filters(self) -> Mapping[str, Collection[str] | str | None]:
        if self.app.fts_search_enabled:
            return {'search': 'Performs a full-text search for the given term'}
        return {}

    def __init__(
        self,
        request: OrgRequest,
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
        for key, values in self.extra_parameters.items():
            self.assert_valid_filter(key)
            if key == 'search':
                term = self.scalarize_value(key, values)
                result.search_widget = DummyDirectorySearchWidget(
                    self.request,
                    term
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

    def by_id(self, id: PKType) -> ExtendedDirectoryEntry | None:
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

        data['content_hash'] = item.content_hash
        data['modified'] = get_modified_iso_format(item)
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


def maybe_uuid(value: str) -> UUID | str:
    try:
        return UUID(value)
    except ValueError:
        return value


class FormApiEndpoint(ApiEndpoint[FormOrExternalLink, UUID | str]):
    app: OrgApp
    request: OrgRequest
    endpoint = 'forms'

    # NOTE: Technically not correct if a form name happens to be a valid
    #       UUID. To be super-robust we would need to always try the raw
    #       string first and then the UUID. But since we don't do anything
    #       to deal with overlaps between forms and external links I don't
    #       think it's worth the effort. Someone would have to maliciously
    #       manipulate the form names in order to cause issues.
    @staticmethod
    def pk_type(value: str) -> UUID | str:
        try:
            return UUID(value)
        except ValueError:
            return value

    @property
    def title(self) -> str:
        return self.request.translate(_('Forms'))

    @property
    def collection(self) -> Any:
        return PaginatedSumCollection(
            self.request,
            (
                (
                    FormCollection(self.session).definitions,
                    FormDefinition
                ),
                (
                    ExternalLinkCollection.for_model(
                        self.session, FormCollection
                    ),
                    ExternalFormLink
                ),
            ),
            batch_size=self.batch_size,
            page=self.page or 0
        )

    def item_data(self, item: FormOrExternalLink) -> dict[str, Any]:
        if isinstance(item, ExternalFormLink):
            return {
                'title': item.title,
                'lead': item.lead,
                'url': item.url,
                'group': item.group,
                'type': 'external',
            }
        data = {
            'title': item.title,
            'lead': item.lead,
            'text': item.text,
            'group': item.group,
            'type': 'internal',
        }
        if item.meta.get('access') == 'mtan' and not self.request.is_manager:
            # remove the part that should not be public
            del data['text']
        return data

    def item_links(self, item: FormOrExternalLink) -> dict[str, Any]:
        if isinstance(item, ExternalFormLink):
            return {'html': item.url}
        return {'html': item}


class ResourceApiEndpoint(ApiEndpoint[ResourceOrExternalLink, UUID]):
    app: OrgApp
    request: OrgRequest
    endpoint = 'resources'
    pk_type = UUID

    @property
    def title(self) -> str:
        return self.request.translate(_('Resources'))

    @property
    def collection(self) -> Any:
        return PaginatedSumCollection(
            self.request,
            (
                (
                    ResourceCollection(self.app.libres_context),
                    Resource
                ),
                (
                    ExternalLinkCollection.for_model(
                        self.session, ResourceCollection
                    ),
                    ExternalResourceLink
                ),
            ),
            batch_size=self.batch_size,
            page=self.page or 0,
        )

    def item_data(
        self, item: ResourceOrExternalLink
    ) -> dict[str, Any]:
        if isinstance(item, ExternalResourceLink):
            return {
                'title': item.title,
                'lead': item.lead,
                'group': item.group,
                'url': item.url,
                'kind': 'external',
            }
        return {
            'title': item.title,
            'lead': getattr(item, 'lead', None),
            'group': item.group,
            'type': item.type,
            'kind': 'internal',
        }

    def item_links(
        self, item: ResourceOrExternalLink
    ) -> dict[str, Any]:
        if isinstance(item, ExternalResourceLink):
            return {'html': item.url}
        return {'html': item}


class PersonApiEndpoint(ApiEndpoint[Person, UUID]):
    app: OrgApp
    request: OrgRequest
    endpoint = 'people'
    pk_type = UUID

    _public_fields: tuple[str, ...] = (
        'academic_title',
        'born',
        'email',
        'first_name',
        'function',
        'last_name',
        'location_address',
        'location_code_city',
        'notes',
        'organisation',
        'parliamentary_group',
        'phone',
        'phone_direct',
        'political_party',
        'postal_address',
        'postal_code_city',
        'profession',
        'salutation',
        'title',
        'website',
    )

    @property
    def title(self) -> str:
        return self.request.translate(_('People'))

    @property
    def collection(self) -> Any:
        return PaginatedCollection(
            self.request,
            PersonCollection(self.session),
            Person,
            batch_size=self.batch_size,
            page=self.page or 0,
        )

    def item_data(self, item: Person) -> dict[str, Any]:
        hidden = self.app.org.hidden_people_fields
        data = {
            attr: getattr(item, attr, None)
            for attr in self._public_fields
            if attr not in hidden
        }
        data['modified'] = get_modified_iso_format(item)
        return data

    def item_links(self, item: Person) -> dict[str, Any]:
        hidden = self.app.org.hidden_people_fields
        result: dict[str, Any] = {'html': item}
        if 'picture_url' not in hidden:
            result['picture_url'] = item.picture_url
        if 'website' not in hidden:
            result['website'] = item.website
        return result
