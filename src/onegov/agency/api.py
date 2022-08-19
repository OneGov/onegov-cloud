from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.api import ApiEndpoint


class PersonApiEndpoint(ApiEndpoint):

    endpoint = 'people'

    @classmethod
    def link(cls, person, request):
        return request.link(
            cls(request.app),
            query_params={'id': person.id.hex}
        )

    @classmethod
    def json(cls, item, request, compact=True):
        if not item:
            return None

        result = {
            '@id': cls.link(item, request),
            'title': item.title
        }
        if compact:
            return result

        result.update({
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
                'picture_url',
                'political_party',
                'profession',
                'salutation',
                'salutation',
                'title',
                'website',
            )
            if attribute not in request.app.org.hidden_people_fields
        })
        result['memberships'] = [
            {
                'title': membership.title,
                'organisation': AgencyApiEndpoint.json(
                    membership.agency, request
                )
            }
            for membership in item.memberships_by_agency
            if (
                membership.access == 'public'
                and membership.published
                and membership.agency
            )
        ]
        return result

    def by_id(self, id_):
        return ExtendedPersonCollection(self.session).by_id(id_)

    @property
    def collection(self):
        result = ExtendedPersonCollection(
            self.session,
            letter=self.get_filter('letter'),
            agency=self.get_filter('agency'),
            page=self.page or 0
        )
        result.batch_size = self.batch_size
        return result


class AgencyApiEndpoint(ApiEndpoint):

    endpoint = 'organisations'

    @classmethod
    def link(cls, agency, request):
        return request.link(
            cls(request.app),
            query_params={'id': str(agency.id)}
        )

    @classmethod
    def json(cls, item, request, compact=True):
        if not item:
            return None

        result = {
            '@id': cls.link(item, request),
            'title': item.title
        }
        if compact:
            return result

        result['portrait'] = item.portrait
        result['organigram_file'] = (
            request.link(item.organigram) if item.organigram_file
            else None
        )
        result['parent'] = cls.json(item.parent, request)
        result['suborganizations'] = [
            cls.json(child, request)
            for child in item.children
            if (child.access == 'public' and child.published)
        ]
        result['memberships'] = [
            {
                'title': membership.title,
                'person': PersonApiEndpoint.json(
                    membership.person,
                    request
                )
            }
            for membership in item.memberships
            if (
                membership.access == 'public'
                and membership.published
                and membership.person
                and membership.person.access == 'public'
                and membership.person.published
            )
        ]
        return result

    def by_id(self, id_):
        return PaginatedAgencyCollection(self.session).by_id(id_)

    @property
    def collection(self):
        result = PaginatedAgencyCollection(
            self.session,
            page=self.page or 0
        )
        result.batch_size = self.batch_size
        return result
