from datetime import datetime

from cached_property import cached_property
from dateutil.parser import isoparse
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import PaginatedMembershipCollection
from onegov.api import ApiEndpoint
from onegov.gis import Coordinates


UPDATE_FILTER_PARAMS = ['updated.gt', 'updated.lt', 'updated.eq',
                        'updated.ge', 'updated.le']


def filter_for_updated(extra_params, result):
    """
    Applies filters for several 'updated' comparisons.
    Refer to UPDATE_FILTER_PARAMS for all filter keywords.

    :param extra_params: url params as dict
    :param result: the results to apply the filters
    :return: filter results
    """
    filters = dict()
    for operator, ts in extra_params.items():
        if not operator.startswith('updated'):
            print(f'Error Invalid updated filter operator \'{operator}\' - '
                  f'ignoring')
            continue
        try:
            ts = isoparse(ts[:16])  # only parse including hours and
            # minutes
        except Exception as ex:
            print(f'Error while parsing timestamp {ts}: {ex}')
            continue
        operator = operator.replace('.', '_')
        filters[operator] = ts
    if filters:
        result = result.for_filter(**filters)
    return result


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
    return dict(lon=geo.lon, lat=geo.lat, zoom=geo.zoom)


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
    filters = []

    @property
    def collection(self):
        result = ExtendedPersonCollection(
            self.session,
            page=self.page or 0
        )

        if self.extra_parameters:  # look for url params to filter
            if 'first_name' in self.extra_parameters.keys():
                firstname = self.extra_parameters.get('first_name')
                result = result.for_filter(first_name=firstname)
            if 'last_name' in self.extra_parameters.keys():
                lastname = self.extra_parameters.get('last_name')
                result = result.for_filter(last_name=lastname)
            if any(key in UPDATE_FILTER_PARAMS for key in
                   self.extra_parameters.keys()):
                result = filter_for_updated(self.extra_parameters, result)

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

        if self.extra_parameters:  # look for url params to filter
            if 'title' in self.extra_parameters.keys():
                title = self.extra_parameters.get('title')
                result = result.for_filter(title=title)

            result = filter_for_updated(self.extra_parameters, result)

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
