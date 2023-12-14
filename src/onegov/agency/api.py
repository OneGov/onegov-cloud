from datetime import datetime

from dateutil.parser import isoparse
from functools import cached_property
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import PaginatedMembershipCollection
from onegov.api import ApiEndpoint, ApiInvalidParamException
from onegov.gis import Coordinates

UPDATE_FILTER_PARAMS = ['updated_gt', 'updated_lt', 'updated_eq',
                        'updated_ge', 'updated_le']


def filter_for_updated(filter_operation, filter_value, result):
    """
    Applies filters for several 'updated' comparisons.
    Refer to UPDATE_FILTER_PARAMS for all filter keywords.

    :param filter_operation: the updated filter operation to be applied. For
    allowed filters refer to UPDATE_FILTER_PARAMS
    :param filter_value: the updated filter value to filter for
    :param result: the results to apply the filters on
    :return: filter result
    """
    try:
        # only parse including hours and minutes
        ts = isoparse(filter_value[:16])
    except Exception as ex:
        raise ApiInvalidParamException(f'Invalid iso timestamp for parameter'
                                       f'\'{filter_operation}\': {ex}') from ex
    return result.for_filter(**{filter_operation: ts})


class ApisMixin:

    @cached_property
    def agency_api(self):
        return AgencyApiEndpoint(self.app)

    @cached_property
    def person_api(self):
        return PersonApiEndpoint(self.app)

    @cached_property
    def membership_api(self):
        return MembershipApiEndpoint(self.app)


def get_geo_location(item):
    geo = item.content.get('coordinates', Coordinates()) or Coordinates()
    return {'lon': geo.lon, 'lat': geo.lat, 'zoom': geo.zoom}


def get_modified_iso_format(item):
    """
    Returns the iso format of the modified or created field of item.

    :param item: db item e.g. agency, people, membership
    :return: str iso representation of item last modification
    """
    return item.modified.isoformat() if isinstance(
        item.modified, datetime) else item.created.isoformat()


class PersonApiEndpoint(ApiEndpoint, ApisMixin):
    endpoint = 'people'
    filters: list[str] = []

    @property
    def collection(self):
        result = ExtendedPersonCollection(
            self.session,
            page=self.page or 0
        )

        for key, value in self.extra_parameters.items():
            valid_params = self.filters + ['first_name',
                                           'last_name'] + UPDATE_FILTER_PARAMS
            if key not in valid_params:
                raise ApiInvalidParamException(
                    f'Invalid url parameter \'{key}\'. Valid params are: '
                    f'{valid_params}')

            # apply different filters
            if key == 'first_name':
                result = result.for_filter(first_name=value)
            if key == 'last_name':
                result = result.for_filter(last_name=value)
            if key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.exclude_hidden = True
        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
        data = {
            attribute: getattr(item, attribute, None)
            for attribute in (
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
            )
            if attribute not in self.app.org.hidden_people_fields
        }

        data['modified'] = get_modified_iso_format(item)
        return data

    def item_links(self, item):
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


class AgencyApiEndpoint(ApiEndpoint, ApisMixin):
    endpoint = 'agencies'
    filters = ['parent']

    @property
    def collection(self):
        result = PaginatedAgencyCollection(
            self.session,
            page=self.page or 0,
            parent=self.get_filter('parent', None, False),
            joinedload=['organigram']
        )

        for key, value in self.extra_parameters.items():
            valid_params = self.filters + ['title'] + UPDATE_FILTER_PARAMS
            if key not in valid_params:
                raise ApiInvalidParamException(
                    f'Invalid url parameter \'{key}\'. Valid params are:'
                    f' {valid_params}')

            # apply different filters
            if key == 'title':
                result = result.for_filter(title=value)
            if key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
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

    def item_links(self, item):
        return {
            'organigram': item.organigram,
            'parent': self.for_item(item.parent_id),
            'children': self.for_filter(parent=str(item.id)),
            'memberships': self.membership_api.for_filter(
                agency=str(item.id)
            )
        }


class MembershipApiEndpoint(ApiEndpoint, ApisMixin):
    endpoint = 'memberships'
    filters = ['agency', 'person']

    @property
    def collection(self):
        result = PaginatedMembershipCollection(
            self.session,
            page=self.page or 0,
            agency=self.get_filter('agency'),
            person=self.get_filter('person'),
        )

        for key, value in self.extra_parameters.items():
            valid_params = self.filters + UPDATE_FILTER_PARAMS
            if key not in valid_params:
                raise ApiInvalidParamException(
                    f'Invalid url parameter \'{key}\'. Valid params are:'
                    f' {valid_params}')

            # apply different filters
            if key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
        return {
            'title': item.title,
            'modified': get_modified_iso_format(item),
        }

    def item_links(self, item):
        return {
            'agency': self.agency_api.for_item(item.agency),
            'person': self.person_api.for_item(item.person)
        }
