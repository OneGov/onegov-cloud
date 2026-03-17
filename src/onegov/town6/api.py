from __future__ import annotations

from functools import cached_property
from uuid import UUID

from onegov.api.models import ApiEndpoint, ApiEndpointItem
from onegov.core.collection import Pagination
from onegov.event.collections import OccurrenceCollection
from onegov.form import FormCollection
from onegov.form.models import FormDefinition
from onegov.gis import Coordinates
from onegov.org.models.directory import (
    ExtendedDirectory, ExtendedDirectoryEntry,
    ExtendedDirectoryEntryCollection)
from onegov.org.models.external_link import (
    ExternalFormLink, ExternalLinkCollection, ExternalResourceLink)
from onegov.org.models.meeting import Meeting, MeetingCollection
from onegov.org.models.page import News, NewsCollection, Topic, TopicCollection
from onegov.org.models.parliament import (
    RISCommission, RISCommissionCollection,
    RISParliamentarian, RISParliamentarianCollection,
    RISParliamentaryGroup, RISParliamentaryGroupCollection)
from onegov.org.models.political_business import (
    PoliticalBusiness, PoliticalBusinessCollection)
from onegov.people import Person
from onegov.people.collections import PersonCollection
from onegov.reservation.collection import ResourceCollection
from onegov.reservation.models import Resource
from onegov.town6 import _
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.inspection import inspect as sa_inspect

from typing import Any, Generic, Self, TypeAlias
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from onegov.town6.app import TownApp
    from onegov.town6.request import TownRequest
    from onegov.event.models import Occurrence
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin
    from typing import Protocol, TypeVar
    from onegov.core.collection import PKType
    from sqlalchemy.orm import Query

    T = TypeVar('T')

    class SupportsQueryAndById(Protocol[T]):
        def query(self) -> Query[T]: ...
        def by_id(self, id: PKType) -> T | None: ...


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


API_BATCH_SIZE = 25
MANAGER_ROLES = {'admin', 'editor'}
LISTING_ACCESSES = {
    'member': ('member', 'mtan', 'public'),
}


def role_for_request(request: TownRequest) -> str:
    return getattr(request.identity, 'role', 'anonymous')


def available_accesses(request: TownRequest) -> tuple[str, ...]:
    role = role_for_request(request)
    if role in MANAGER_ROLES:
        return ()
    return LISTING_ACCESSES.get(role, ('mtan', 'public'))


def apply_visibility_filters(
    request: TownRequest,
    query: Query[T],
    model_class: Any,
) -> Query[T]:
    accesses = available_accesses(request)
    if accesses and hasattr(model_class, 'access'):
        query = query.filter(or_(
            *(
                model_class.meta['access'].astext == access
                for access in accesses
            ),
            model_class.meta['access'].is_(None)
        ))

    if (
        role_for_request(request) not in MANAGER_ROLES
        and hasattr(model_class, 'publication_started')
        and hasattr(model_class, 'publication_ended')
    ):
        query = query.filter(
            model_class.publication_started == True,
            model_class.publication_ended == False
        )

    return query


class FilteredCollection(Generic[T]):

    def __init__(
        self,
        request: TownRequest,
        collection: Any,
        model_class: type[T],
        query_transform: Callable[[Query[T]], Query[T]],
    ) -> None:
        self.request = request
        self.collection = collection
        self.model_class = model_class
        self.query_transform = query_transform

    def query(self) -> Query[T]:
        return self.query_transform(self.collection.query())

    def by_id(self, id: PKType) -> T | None:
        try:
            if callable(getattr(self.collection, 'by_id', None)):
                item = self.collection.by_id(id)
                if item is not None:
                    return item if self.request.is_visible(item) else None

            primary_key = sa_inspect(self.model_class).primary_key[0]
            return self.query().filter(
                primary_key == self._normalize_id(id)
            ).first()
        except SQLAlchemyError:
            return None

    @staticmethod
    def _normalize_id(id: PKType) -> PKType:
        if isinstance(id, str):
            try:
                return UUID(id)
            except ValueError:
                return id
        return id


class PaginatedCollection(Pagination[T], Generic[T]):

    def __init__(
        self,
        collection: SupportsQueryAndById[T],
        page: int = 0,
        batch_size: int = API_BATCH_SIZE,
    ) -> None:
        self.collection = collection
        self.page = page
        self.batch_size = batch_size

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.collection is other.collection
            and self.page == other.page
        )

    def by_id(self, id: PKType) -> T | None:
        return self.collection.by_id(id)

    def subset(self) -> Query[T]:
        return self.collection.query()

    def page_by_index(self, index: int) -> PaginatedCollection[T]:
        return self.__class__(
            self.collection,
            page=index,
            batch_size=self.batch_size,
        )

    @property
    def page_index(self) -> int:
        return self.page


class PaginatedSumCollection(Pagination[T], Generic[T]):

    def __init__(
        self,
        collections: Sequence[SupportsQueryAndById[T]],
        page: int = 0,
        batch_size: int = API_BATCH_SIZE,
    ) -> None:
        self.collections = tuple(collections)
        self.page = page
        self.batch_size = batch_size

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.collections == other.collections
            and self.page == other.page
        )

    def by_id(self, id: PKType) -> T | None:
        for collection in self.collections:
            item = collection.by_id(id)
            if item is not None:
                return item
        return None

    def subset(self) -> Query[T]:
        raise NotImplementedError(
            'PaginatedSumCollection does not expose a single subset query'
        )

    @cached_property
    def counts(self) -> tuple[int, ...]:
        return tuple(
            collection.query().order_by(None).count()
            for collection in self.collections
        )

    @cached_property
    def subset_count(self) -> int:
        return sum(self.counts)

    @cached_property
    def batch(self) -> tuple[T, ...]:
        offset = self.offset
        remaining = self.batch_size
        items: list[T] = []

        for collection, count in zip(self.collections, self.counts):
            if remaining <= 0:
                break
            if offset >= count:
                offset -= count
                continue

            query = collection.query().offset(offset).limit(remaining)
            batch = tuple(query)
            items.extend(batch)
            remaining -= len(batch)
            offset = 0

        return tuple(items)

    def page_by_index(self, index: int) -> PaginatedSumCollection[T]:
        return self.__class__(
            self.collections,
            page=index,
            batch_size=self.batch_size,
        )

    @property
    def page_index(self) -> int:
        return self.page


def visible_collection(
    request: TownRequest,
    collection: Any,
    model_class: type[T],
    *,
    order_by: Any | None = None,
) -> FilteredCollection[T]:
    def transform(query: Query[T]) -> Query[T]:
        query = apply_visibility_filters(request, query, model_class)
        if order_by is not None:
            query = query.order_by(order_by)
        return query

    return FilteredCollection(request, collection, model_class, transform)


class EventApiEndpoint(ApiEndpoint['Occurrence']):
    app: TownApp
    endpoint = 'events'

    @property
    def title(self) -> str:
        return self.request.translate(_('Events'))

    @property
    def description(self) -> str | None:
        return self.app.org.event_header_html or self.app.org.event_footer_html

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
    filters = set()

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
    filters = set()
    endpoint: str

    def __init__(
        self,
        request: TownRequest,
        name: str,
        extra_parameters: dict[str, str | None] | None = None,
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


FormOrExternalLink: TypeAlias = FormDefinition | ExternalFormLink
ResourceOrExternalLink: TypeAlias = Resource | ExternalResourceLink


class FormApiEndpoint(ApiEndpoint[FormOrExternalLink]):
    app: TownApp
    endpoint = 'forms'

    @property
    def title(self) -> str:
        return self.request.translate(_('Forms'))

    @property
    def collection(self) -> Any:
        return PaginatedSumCollection(
            (
                visible_collection(
                    self.request,
                    FormCollection(self.session).definitions,
                    FormDefinition,
                    order_by=FormDefinition.order,
                ),
                visible_collection(
                    self.request,
                    ExternalLinkCollection.for_model(
                        self.session, FormCollection
                    ),
                    ExternalFormLink,
                    order_by=ExternalFormLink.order,
                ),
            ),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
        )

    def by_id(self, id: PKType) -> FormOrExternalLink | None:
        return self.collection.by_id(id)

    def item_data(self, item: FormOrExternalLink) -> dict[str, Any]:
        if isinstance(item, ExternalFormLink):
            return {
                'title': item.title,
                'lead': item.lead,
                'group': item.group,
                'url': item.url,
                'type': 'external',
            }
        return {
            'title': item.title,
            'lead': item.lead,
            'text': str(item.text) if item.text else None,
            'group': item.group,
            'type': 'internal',
        }

    def item_links(self, item: FormOrExternalLink) -> dict[str, Any]:
        if isinstance(item, ExternalFormLink):
            return {'html': item.url}
        return {'html': item}


class ResourceApiEndpoint(ApiEndpoint[ResourceOrExternalLink]):
    app: TownApp
    endpoint = 'resources'

    @property
    def title(self) -> str:
        return self.request.translate(_('Resources'))

    @property
    def collection(self) -> Any:
        return PaginatedSumCollection(
            (
                visible_collection(
                    self.request,
                    ResourceCollection(self.app.libres_context),
                    Resource,
                    order_by=Resource.title,
                ),
                visible_collection(
                    self.request,
                    ExternalLinkCollection.for_model(
                        self.session, ResourceCollection
                    ),
                    ExternalResourceLink,
                    order_by=ExternalResourceLink.order,
                ),
            ),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
        )

    def by_id(self, id: PKType) -> ResourceOrExternalLink | None:
        return self.collection.by_id(id)

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


class PersonApiEndpoint(ApiEndpoint[Person]):
    app: TownApp
    endpoint = 'people'

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
            visible_collection(
                self.request,
                PersonCollection(self.session),
                Person,
            ),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
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


class MeetingApiEndpoint(ApiEndpoint[Meeting]):
    app: TownApp
    endpoint = 'meetings'

    @property
    def title(self) -> str:
        return self.request.translate(_('Meetings'))

    @property
    def collection(self) -> Any:
        return PaginatedCollection(
            visible_collection(
                self.request,
                MeetingCollection(self.session),
                Meeting,
            ),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
        )

    def item_data(self, item: Meeting) -> dict[str, Any]:
        return {
            'title': item.title,
            'start_datetime': (
                item.start_datetime.isoformat()
                if item.start_datetime else None
            ),
            'end_datetime': (
                item.end_datetime.isoformat()
                if item.end_datetime else None
            ),
            'address': str(item.address) if item.address else None,
            'description': str(item.description) if item.description else None,
            'audio_link': item.audio_link or None,
            'video_link': item.video_link or None,
        }

    def item_links(self, item: Meeting) -> dict[str, Any]:
        return {'html': item}


class PoliticalBusinessApiEndpoint(ApiEndpoint[PoliticalBusiness]):
    app: TownApp
    endpoint = 'political_businesses'

    @property
    def title(self) -> str:
        return self.request.translate(_('Political Businesses'))

    @property
    def collection(self) -> Any:
        return PaginatedCollection(
            visible_collection(
                self.request,
                PoliticalBusinessCollection(self.request),
                PoliticalBusiness,
            ),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
        )

    def item_data(self, item: PoliticalBusiness) -> dict[str, Any]:
        return {
            'title': item.title,
            'number': item.number,
            'political_business_type': item.political_business_type,
            'status': item.status,
            'entry_date': (
                item.entry_date.isoformat() if item.entry_date else None
            ),
            'display_name': item.display_name,
        }

    def item_links(self, item: PoliticalBusiness) -> dict[str, Any]:
        return {'html': item}


class RISParliamentarianApiEndpoint(ApiEndpoint[RISParliamentarian]):
    app: TownApp
    endpoint = 'parliamentarians'

    @property
    def title(self) -> str:
        return self.request.translate(_('Parliamentarians'))

    @property
    def collection(self) -> Any:
        return PaginatedCollection(
            RISParliamentarianCollection(self.session),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
        )

    def item_data(self, item: RISParliamentarian) -> dict[str, Any]:
        return {
            'first_name': item.first_name,
            'last_name': item.last_name,
            'title': item.title,
            'party': item.party,
            'active': item.active,
        }

    def item_links(self, item: RISParliamentarian) -> dict[str, Any]:
        return {
            'html': item,
            'picture': item.picture,
        }


class RISCommissionApiEndpoint(ApiEndpoint[RISCommission]):
    app: TownApp
    endpoint = 'commissions'

    @property
    def title(self) -> str:
        return self.request.translate(_('Commissions'))

    @property
    def collection(self) -> Any:
        return PaginatedCollection(
            RISCommissionCollection(self.session),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
        )

    def item_data(self, item: RISCommission) -> dict[str, Any]:
        return {
            'name': item.name,
            'description': str(item.description) if item.description else None,
        }

    def item_links(self, item: RISCommission) -> dict[str, Any]:
        return {'html': item}


class RISParliamentaryGroupApiEndpoint(ApiEndpoint[RISParliamentaryGroup]):
    app: TownApp
    endpoint = 'parliamentary_groups'

    @property
    def title(self) -> str:
        return self.request.translate(_('Parliamentary groups'))

    @property
    def collection(self) -> Any:
        return PaginatedCollection(
            RISParliamentaryGroupCollection(self.session),
            page=self.page or 0,
            batch_size=API_BATCH_SIZE,
        )

    def item_data(self, item: RISParliamentaryGroup) -> dict[str, Any]:
        return {
            'name': item.name,
            'description': str(item.description) if item.description else None,
        }

    def item_links(self, item: RISParliamentaryGroup) -> dict[str, Any]:
        return {'html': item}
