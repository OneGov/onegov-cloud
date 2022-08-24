from cached_property import cached_property
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

    @property
    def collection(self):
        result = ExtendedPersonCollection(
            self.session,
            page=self.page or 0
        )
        result.exclude_hidden = True
        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
        return {
            attribute: getattr(item, attribute, None)
            for attribute in (
                'academic_title',
                'address',
                'born',
                'email',
                'first_name',
                'function',
                'last_name',
                'notes',
                'parliamentary_group',
                'phone_direct',
                'phone',
                'political_party',
                'profession',
                'salutation',
                'salutation',
                'title',
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
            parent=self.get_filter('parent'),
        )
        result.exclude_hidden = True
        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
        return {
            'title': item.title,
            'portrait': item.portrait
        }

    def item_links(self, item):
        return {
            'organigram': item.organigram,
            'parent': self.for_item(item.parent),
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
            person=self.get_filter('person')
        )
        result.exclude_hidden = True
        result.batch_size = self.batch_size
        return result

    def item_data(self, item):
        return {
            'title': item.title
        }

    def item_links(self, item):
        result = {}
        result['agency'] = None
        if item.agency:
            if item.agency.published and item.agency.access == 'public':
                result['agency'] = self.agency_api.for_item(item.agency)
        result['person'] = None
        if item.person:
            if item.person.published and item.person.access == 'public':
                result['person'] = self.person_api.for_item(item.person)
        return result
