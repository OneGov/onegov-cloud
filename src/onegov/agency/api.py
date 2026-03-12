from __future__ import annotations

from dateutil.parser import isoparse
from functools import cached_property
from onegov.agency import _
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import PaginatedMembershipCollection
from onegov.agency.forms.person import AuthenticatedPersonMutationForm
from onegov.api import ApiEndpoint, ApiInvalidParamException
from onegov.api.utils import is_authorized
from onegov.gis import Coordinates


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.forms import PersonMutationForm
    from onegov.core.request import CoreRequest
    from onegov.agency.app import AgencyApp
    from onegov.agency.models import ExtendedAgency
    from onegov.agency.models import ExtendedAgencyMembership
    from onegov.agency.models import ExtendedPerson
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin
    from typing import TypeVar

    T = TypeVar('T')


UPDATE_FILTER_PARAMS = frozenset((
    'updated_gt',
    'updated_lt',
    'updated_eq',
    'updated_ge',
    'updated_le'
))


def filter_for_updated(
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
        isoparse(filter_value[:16])
    except Exception as ex:
        raise ApiInvalidParamException(f'Invalid iso timestamp for parameter'
                                       f"'{filter_operation}': {ex}") from ex
    return result.for_filter(**{filter_operation: filter_value[:16]})


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


class PersonApiEndpoint(ApiEndpoint['ExtendedPerson'], ApisMixin):
    request: CoreRequest
    app: AgencyApp
    endpoint = 'people'
    filters = {'first_name', 'last_name'} | UPDATE_FILTER_PARAMS
    form_class = AuthenticatedPersonMutationForm

    @property
    def title(self) -> str:
        return self.request.translate(_('People'))

    @property
    def collection(self) -> ExtendedPersonCollection:
        result = ExtendedPersonCollection(
            self.session,
            page=self.page or 0
        )

        for key, value in self.extra_parameters.items():
            self.assert_valid_filter(key)

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
        result = {
            attribute: getattr(item, attribute, None)
            for attribute in (
                'picture_url',
                'website',
            )
            if attribute not in self.app.org.hidden_people_fields
        }
        result['memberships'] = self.membership_api.for_filter(
            person=item.id.hex
        )
        return result

    def apply_changes(
        self,
        item: ExtendedPerson,
        form: PersonMutationForm
    ) -> None:

        # FIXME: circular import
        from onegov.agency.views.people import do_report_person_change
        do_report_person_change(item, form.meta.request, form)


class AgencyApiEndpoint(ApiEndpoint['ExtendedAgency'], ApisMixin):
    request: CoreRequest
    app: AgencyApp
    endpoint = 'agencies'
    filters = {'parent', 'title'} | UPDATE_FILTER_PARAMS

    @property
    def title(self) -> str:
        return self.request.translate(_('Agencies'))

    @property
    def collection(self) -> PaginatedAgencyCollection:
        result = PaginatedAgencyCollection(
            self.session,
            page=self.page or 0,
            parent=self.get_filter('parent', None, False),
            joinedload=['organigram'],
            undefer=['content']
        )

        for key, value in self.extra_parameters.items():
            self.assert_valid_filter(key)
            # apply different filters
            if key == 'title':
                result = result.for_filter(title=value)
            elif key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.batch_size = self.batch_size
        return result

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
            'organigram': item.organigram,
            'parent': self.for_item_id(item.parent_id),
            'children': self.for_filter(parent=str(item.id)),
            'memberships': self.membership_api.for_filter(
                agency=str(item.id)
            )
        }


class MembershipApiEndpoint(
    ApiEndpoint['ExtendedAgencyMembership'],
    ApisMixin
):

    request: CoreRequest
    app: AgencyApp
    endpoint = 'memberships'
    filters = {'agency', 'person'} | UPDATE_FILTER_PARAMS

    @property
    def collection(self) -> PaginatedMembershipCollection:
        result = PaginatedMembershipCollection(
            self.session,
            page=self.page or 0,
            agency=self.get_filter('agency'),
            person=self.get_filter('person'),
        )

        for key, value in self.extra_parameters.items():
            self.assert_valid_filter(key)

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
            'agency': self.agency_api.for_item_id(item.agency_id),
            'person': self.person_api.for_item_id(item.person_id)
        }
