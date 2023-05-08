from cached_property import cached_property
from dateutil.parser import isoparse
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import PaginatedMembershipCollection
from onegov.api import ApiEndpoint


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


class PersonApiEndpoint(ApiEndpoint, ApisMixin):

    endpoint = 'people'
    filters = []
    UPDATE_FILTER_PARAMS = ['updated.gt', 'updated.lt', 'updated.eq',
                            'updated.ge', 'updated.le']

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

            filters = dict()
            for operator, ts in self.extra_parameters.items():
                if operator not in self.UPDATE_FILTER_PARAMS:
                    print(f'Error Invalid filter operator {operator} - '
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

        result.exclude_hidden = True
        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
        return {
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
        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
        return {
            'title': item.title,
            'portrait': item.portrait,
            'location_address': item.location_address,
            'location_code_city': item.location_code_city,
            'postal_address': item.postal_address,
            'postal_code_city': item.postal_code_city,
            'website': item.website,
            'email': item.email,
            'phone': item.phone,
            'phone_direct': item.phone_direct,
            'opening_hours': item.opening_hours,
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
            'title': item.title
        }

    def item_links(self, item):
        return {
            'agency': self.agency_api.for_item(item.agency),
            'person': self.person_api.for_item(item.person)
        }
