from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import ExtendedPerson
from onegov.core.collection import GenericCollection
from onegov.core.collection import Pagination
from sqlalchemy import or_
from sqlalchemy.orm import joinedload


class PaginatedMembershipCollection(GenericCollection, Pagination):

    def __init__(self, session, page=0, agency=None, person=None,
                 exclude_hidden=True):
        super().__init__(session)
        self.page = page
        self.agency = agency
        self.person = person
        self.exclude_hidden = exclude_hidden

    @property
    def model_class(self):
        return ExtendedAgencyMembership

    def __eq__(self, other):
        return (
            other.page == self.page
            and other.agency == self.agency
            and other.person == self.person
        )

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, page=index)

    def query(self):
        query = super().query()

        if self.exclude_hidden:
            query = query.options(joinedload(ExtendedAgencyMembership.agency))
            query = query.options(joinedload(ExtendedAgencyMembership.person))

            query = query.filter(
                or_(
                    ExtendedAgencyMembership.meta['access'] == 'public',
                    ExtendedAgencyMembership.meta['access'] == None,
                ),
                ExtendedAgencyMembership.published.is_(True)
            )

            query = query.filter(
                ExtendedAgencyMembership.agency_id.isnot(None)
            )
            query = query.filter(
                ExtendedAgency.id == ExtendedAgencyMembership.agency_id,
                or_(
                    ExtendedAgency.meta['access'] == 'public',
                    ExtendedAgency.meta['access'] == None,
                ),
                ExtendedAgency.published.is_(True)
            )

            query = query.filter(
                ExtendedAgencyMembership.person_id.isnot(None)
            )
            query = query.filter(
                ExtendedPerson.id == ExtendedAgencyMembership.person_id,
                or_(
                    ExtendedPerson.meta['access'] == 'public',
                    ExtendedPerson.meta['access'] == None,
                ),
                ExtendedPerson.published.is_(True)
            )

        if self.agency:
            query = query.filter(
                ExtendedAgencyMembership.agency_id == self.agency
            )

        if self.person:
            query = query.filter(
                ExtendedAgencyMembership.person_id == self.person
            )

        return query
