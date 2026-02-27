from __future__ import annotations

from functools import cached_property
from onegov.api.models import ApiEndpoint, ApiEndpointItem
from onegov.core.collection import GenericCollection, Pagination
from onegov.event.collections import OccurrenceCollection
from onegov.form.models import FormDefinition
from onegov.gis import Coordinates
from onegov.org.models.directory import (
    ExtendedDirectory, ExtendedDirectoryEntry,
    ExtendedDirectoryEntryCollection)
from onegov.org.models.external_link import (
    ExternalFormLink, ExternalResourceLink)
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
from sqlalchemy.exc import SQLAlchemyError

from typing import Any, Self
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.app import TownApp
    from onegov.town6.request import TownRequest
    from onegov.event.models import Occurrence
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin
    from typing import TypeVar
    from onegov.core.collection import PKType
    from sqlalchemy.orm import Query, Session

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


class PaginatedFormDefinitionCollection(
    GenericCollection[FormDefinition],
    Pagination[FormDefinition]
):

    def __init__(self, session: Session, page: int = 0) -> None:
        super().__init__(session)
        self.page = page
        self.batch_size = 25

    @property
    def model_class(self) -> type[FormDefinition]:
        return FormDefinition

    def subset(self) -> Query[FormDefinition]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page


class PaginatedResourceCollection:

    def __init__(
        self,
        resource_collection: ResourceCollection,
        page: int = 0
    ) -> None:
        self.resource_collection = resource_collection
        self.session = resource_collection.session
        self.page = page
        self.batch_size = 25

    def by_id(self, id: PKType) -> Resource | None:
        return self.resource_collection.by_id(id)  # type: ignore

    def subset(self) -> Query[Resource]:
        return self.resource_collection.query().order_by(Resource.title)

    @cached_property
    def cached_subset(self) -> Query[Resource]:
        return self.subset()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.resource_collection, page=index
        )

    @property
    def subset_count(self) -> int:
        return self.cached_subset.count()

    @property
    def offset(self) -> int:
        return self.page * self.batch_size

    @property
    def pages_count(self) -> int:
        if not self.subset_count:
            return 0
        return max(1, -(-self.subset_count // self.batch_size))

    @property
    def batch(self) -> tuple[Resource, ...]:
        return tuple(
            self.cached_subset.offset(self.offset).limit(self.batch_size)
        )

    @property
    def previous(self) -> Self | None:
        if self.page > 0:
            return self.page_by_index(self.page - 1)
        return None

    @property
    def next(self) -> Self | None:
        if self.page < self.pages_count - 1:
            return self.page_by_index(self.page + 1)
        return None


class PaginatedPersonCollection(
    PersonCollection,
    Pagination[Person]
):

    def __init__(self, session: Session, page: int = 0) -> None:
        PersonCollection.__init__(self, session)
        self.page = page
        self.batch_size = 25

    def subset(self) -> Query[Person]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page


class PaginatedMeetingCollection(
    MeetingCollection,
    Pagination[Meeting]
):

    def __init__(self, session: Session, page: int = 0) -> None:
        MeetingCollection.__init__(self, session)
        self.page = page
        self.batch_size = 25

    def subset(self) -> Query[Meeting]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page


class PaginatedParliamentarianCollection(
    RISParliamentarianCollection,
    Pagination[RISParliamentarian]
):

    def __init__(self, session: Session, page: int = 0) -> None:
        RISParliamentarianCollection.__init__(self, session)
        self.page = page
        self.batch_size = 25

    def subset(self) -> Query[RISParliamentarian]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page


class PaginatedCommissionCollection(
    RISCommissionCollection,
    Pagination[RISCommission]
):

    def __init__(self, session: Session, page: int = 0) -> None:
        RISCommissionCollection.__init__(self, session)
        self.page = page
        self.batch_size = 25

    def subset(self) -> Query[RISCommission]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page


class PaginatedParliamentaryGroupCollection(
    RISParliamentaryGroupCollection,
    Pagination[RISParliamentaryGroup]
):

    def __init__(self, session: Session, page: int = 0) -> None:
        RISParliamentaryGroupCollection.__init__(self, session)
        self.page = page
        self.batch_size = 25

    def subset(self) -> Query[RISParliamentaryGroup]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page


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


FormOrExternalLink = FormDefinition | ExternalFormLink
ResourceOrExternalLink = Resource | ExternalResourceLink


class FormApiEndpoint(ApiEndpoint[FormOrExternalLink]):
    app: TownApp
    endpoint = 'forms'

    @property
    def title(self) -> str:
        return self.request.translate(_('Forms'))

    @property
    def collection(self) -> Any:
        return PaginatedFormDefinitionCollection(
            self.session, page=self.page or 0
        )

    @property
    def batch(self) -> dict[ApiEndpointItem[FormOrExternalLink],
                            FormOrExternalLink]:
        result: dict[ApiEndpointItem[FormOrExternalLink],
                     FormOrExternalLink] = {}
        for item in self.collection.batch:
            endpoint_item = self.for_item(item)
            if endpoint_item:
                result[endpoint_item] = item
        for ext in self.session.query(ExternalFormLink).all():
            endpoint_item = self.for_item(ext)
            if endpoint_item:
                result[endpoint_item] = ext
        return result

    def by_id(self, id: PKType) -> FormOrExternalLink | None:
        try:
            item = self.session.query(FormDefinition).filter_by(
                name=id
            ).first()
            if item:
                return item
            return self.session.query(ExternalFormLink).get(id)
        except SQLAlchemyError:
            return None

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
        resource_collection = ResourceCollection(self.app.libres_context)
        return PaginatedResourceCollection(
            resource_collection, page=self.page or 0
        )

    @property
    def batch(self) -> dict[ApiEndpointItem[ResourceOrExternalLink],
                            ResourceOrExternalLink]:
        result: dict[ApiEndpointItem[ResourceOrExternalLink],
                     ResourceOrExternalLink] = {}
        for item in self.collection.batch:
            endpoint_item = self.for_item(item)
            if endpoint_item:
                result[endpoint_item] = item
        for ext in self.session.query(ExternalResourceLink).all():
            endpoint_item = self.for_item(ext)
            if endpoint_item:
                result[endpoint_item] = ext
        return result

    def by_id(self, id: PKType) -> ResourceOrExternalLink | None:
        try:
            resource_collection = ResourceCollection(self.app.libres_context)
            item = resource_collection.by_id(id)  # type: ignore
            if item:
                return item
            return self.session.query(ExternalResourceLink).get(id)
        except SQLAlchemyError:
            return None

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
        return PaginatedPersonCollection(
            self.session, page=self.page or 0
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
        return PaginatedMeetingCollection(
            self.session, page=self.page or 0
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
        return PoliticalBusinessCollection(
            self.request, page=self.page or 0
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
        return PaginatedParliamentarianCollection(
            self.session, page=self.page or 0
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
        return PaginatedCommissionCollection(
            self.session, page=self.page or 0
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
        return PaginatedParliamentaryGroupCollection(
            self.session, page=self.page or 0
        )

    def item_data(self, item: RISParliamentaryGroup) -> dict[str, Any]:
        return {
            'name': item.name,
            'description': str(item.description) if item.description else None,
        }

    def item_links(self, item: RISParliamentaryGroup) -> dict[str, Any]:
        return {'html': item}
