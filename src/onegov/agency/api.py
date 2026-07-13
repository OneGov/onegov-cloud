from __future__ import annotations

from dateutil.parser import isoparse
from functools import cached_property
from onegov.agency import _
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import PaginatedMembershipCollection
from onegov.agency.forms.person import AuthenticatedPersonMutationForm
from onegov.agency.models import ExtendedAgency
from onegov.api import ApiEndpoint, ApiInvalidParamException
from onegov.api.utils import is_authorized
from onegov.gis import Coordinates
from sqlalchemy.orm.attributes import set_committed_value
from uuid import UUID


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.agency.forms import PersonMutationForm
    from onegov.api.models import ApiEndpointItem
    from onegov.core.request import CoreRequest
    from onegov.agency.app import AgencyApp
    from onegov.agency.models import ExtendedAgencyMembership
    from onegov.agency.models import ExtendedPerson
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin


UPDATE_FILTER_PARAMS = frozenset((
    'updated_gt',
    'updated_lt',
    'updated_eq',
    'updated_ge',
    'updated_le'
))
UPDATE_FILTER_PROMPT = 'ISO-8601 encoded datetime'


def filter_for_updated[T](
    filter_operation: str,
    filter_value: str | None,
    result: T
) -> T:
    """
    Applies filters for several 'updated' comparisons.
    Refer to UPDATE_FILTER_PARAMS for all filter keywords.

    :param filter_operation: the updated filter operation to be applied. For
        allowed filters refer to UPDATE_FILTER_PARAMS
    :param filter_value: the updated filter value to filter for
    :param result: the results to apply the filters on
    :return: filter result
    """
    assert hasattr(result, 'for_filter')

    if filter_value is None:
        return result.for_filter(**{filter_operation: None})

    try:
        # only parse including hours and minutes
        parsed = isoparse(filter_value[:16])
    except Exception as ex:
        raise ApiInvalidParamException(
            f'Invalid ISO-8601 datetime for parameter {filter_operation!r}'
        ) from ex
    return result.for_filter(**{filter_operation: parsed})


class ApisMixin:

    request: CoreRequest

    @cached_property
    def agency_api(self) -> AgencyApiEndpoint:
        return AgencyApiEndpoint(self.request)

    @cached_property
    def person_api(self) -> PersonApiEndpoint:
        return PersonApiEndpoint(self.request)

    @cached_property
    def membership_api(self) -> MembershipApiEndpoint:
        return MembershipApiEndpoint(self.request)


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


class PersonApiEndpoint(ApiEndpoint['ExtendedPerson', UUID], ApisMixin):
    request: CoreRequest
    app: AgencyApp
    endpoint = 'people'
    filters = {
        'first_name': None,
        'last_name': None
    } | dict.fromkeys(UPDATE_FILTER_PARAMS, UPDATE_FILTER_PROMPT)
    form_class = AuthenticatedPersonMutationForm
    pk_type = UUID

    @property
    def title(self) -> str:
        return self.request.translate(_('People'))

    @property
    def collection(self) -> ExtendedPersonCollection:
        result = ExtendedPersonCollection(
            self.session,
            page=self.page or 0
        )

        for key, values in self.extra_parameters.items():
            self.assert_valid_filter(key)
            # scalarize the value since all our filters are scalar
            value = self.scalarize_value(key, values)

            # apply different filters
            if key == 'first_name':
                result = result.for_filter(first_name=value)
            elif key == 'last_name':
                result = result.for_filter(last_name=value)
            elif key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.exclude_hidden = True
        result.batch_size = self.batch_size
        return result

    @property
    def _public_item_data(self) -> tuple[str, ...]:
        return tuple(attribute for attribute in (
            'academic_title',
            'born',
            'email',
            'first_name',
            'function',
            'last_name',
            'location_address',
            'location_code_city',
            'notes',
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
        ) if attribute not in self.app.org.hidden_people_fields)

    def item_data(self, item: ExtendedPerson) -> dict[str, Any]:
        public_data = self._public_item_data
        if self.request is not None and is_authorized(self.request):
            # Authorized users get all fields including external_user_id
            data = {
                attribute: getattr(item, attribute, None)
                for attribute in (*public_data, 'external_user_id')
            }
        else:
            # Non-authenticated users only get non-hidden fields
            data = {
                attribute: getattr(item, attribute, None)
                for attribute in public_data
            }

        data['modified'] = get_modified_iso_format(item)
        return data

    def item_links(self, item: ExtendedPerson) -> dict[str, Any]:
        picture_url = (
            item.picture_url
            if 'picture_url' not in self.app.org.hidden_people_fields
            else None
        )
        website = (
            item.website
            if 'website' not in self.app.org.hidden_people_fields
            else None
        )
        result = {
            'html': item,
            'picture_url': picture_url,
            'website': website,
            'memberships': self.membership_api.for_filter(
                person=[item.id.hex]
            )
        }
        return result

    def apply_changes(
        self,
        item: ExtendedPerson,
        form: PersonMutationForm
    ) -> None:

        # FIXME: circular import
        from onegov.agency.views.people import do_report_person_change
        do_report_person_change(item, form.meta.request, form)


class AgencyApiEndpoint(ApiEndpoint['ExtendedAgency', int], ApisMixin):
    request: CoreRequest
    app: AgencyApp
    endpoint = 'agencies'
    filters = {
        'parent': None,
        'title': None
    } | dict.fromkeys(UPDATE_FILTER_PARAMS, UPDATE_FILTER_PROMPT)
    pk_type = int

    @property
    def title(self) -> str:
        return self.request.translate(_('Agencies'))

    @property
    def collection(self) -> PaginatedAgencyCollection:
        result = PaginatedAgencyCollection(
            self.session,
            page=self.page or 0,
            parent=self.get_filter('parent', None, False, coerce=int),
            joinedload=['organigram', 'parent'],
            undefer=['content']
        )

        for key, values in self.extra_parameters.items():
            self.assert_valid_filter(key)
            # scalarize the value since all our filters are scalar
            value = self.scalarize_value(key, values)
            # apply different filters
            if key == 'title':
                result = result.for_filter(title=value)
            elif key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.batch_size = self.batch_size
        return result

    @property
    def batch(
        self
    ) -> dict[ApiEndpointItem[ExtendedAgency, int], ExtendedAgency]:
        result = super().batch
        self.preload_ancestors(result.values())
        return result

    def preload_ancestors(self, agencies: Iterable[ExtendedAgency]) -> None:
        """ Bulk loads all ancestors of the given agencies and wires up their
        ``parent`` relationship, so walking the parent chain (e.g. to build
        links) doesn't emit a query per ancestor. """

        session = self.session
        by_id: dict[int, ExtendedAgency] = {}
        pending: set[int] = set()
        for agency in agencies:
            by_id[agency.id] = agency
            # the direct parent is already eager loaded (see `collection`)
            parent = agency.parent
            if parent is not None:
                by_id[parent.id] = parent
                if (
                    parent.parent_id is not None
                    and parent.parent_id not in by_id
                ):
                    pending.add(parent.parent_id)

        # load the remaining ancestors one level at a time (a handful of
        # queries bound by the tree depth, instead of one query per ancestor)
        while pending:
            ancestors = session.query(ExtendedAgency).filter(
                ExtendedAgency.id.in_(pending)
            ).all()
            pending = set()
            for ancestor in ancestors:
                by_id[ancestor.id] = ancestor
                if (
                    ancestor.parent_id is not None
                    and ancestor.parent_id not in by_id
                ):
                    pending.add(ancestor.parent_id)

        # populate the parent relationship from the loaded set, so accessing
        # it later resolves in-memory rather than triggering a lazy load
        for agency in by_id.values():
            if agency.parent_id is not None:
                parent = by_id.get(agency.parent_id)
                if parent is not None:
                    set_committed_value(agency, 'parent', parent)

    def item_data(self, item: ExtendedAgency) -> dict[str, Any]:
        return {
            'title': item.title,
            'portrait': item.portrait,
            'location_address': item.location_address,
            'location_code_city': item.location_code_city,
            'modified': get_modified_iso_format(item),
            'postal_address': item.postal_address,
            'postal_code_city': item.postal_code_city,
            'website': item.website,
            'email': item.email,
            'phone': item.phone,
            'phone_direct': item.phone_direct,
            'opening_hours': item.opening_hours,
            'geo_location': get_geo_location(item),
        }

    def item_links(self, item: ExtendedAgency) -> dict[str, Any]:
        return {
            'html': item,
            'organigram': item.organigram,
            'parent': self.for_item_id(item.parent_id),
            'children': self.for_filter(parent=[str(item.id)]),
            'memberships': self.membership_api.for_filter(
                agency=[str(item.id)]
            )
        }


class MembershipApiEndpoint(
    ApiEndpoint['ExtendedAgencyMembership', UUID],
    ApisMixin
):

    request: CoreRequest
    app: AgencyApp
    endpoint = 'memberships'
    filters = {
        'agency': None,
        'person': None
    } | dict.fromkeys(UPDATE_FILTER_PARAMS, UPDATE_FILTER_PROMPT)
    pk_type = UUID

    @property
    def collection(self) -> PaginatedMembershipCollection:
        result = PaginatedMembershipCollection(
            self.session,
            page=self.page or 0,
            agency=self.get_filter('agency', coerce=int),
            person=self.get_filter('person', coerce=UUID),
        )

        for key, values in self.extra_parameters.items():
            self.assert_valid_filter(key)
            # scalarize the value since all our filters are scalar
            value = self.scalarize_value(key, values)

            # apply different filters
            if key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.batch_size = self.batch_size
        return result

    def item_data(self, item: ExtendedAgencyMembership) -> dict[str, Any]:
        return {
            'title': item.title,
            'modified': get_modified_iso_format(item),
        }

    def item_links(self, item: ExtendedAgencyMembership) -> dict[str, Any]:
        return {
            'html': item,
            'agency': self.agency_api.for_item_id(item.agency_id),
            'person': self.person_api.for_item_id(item.person_id)
        }
