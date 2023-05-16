from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import ExtendedPerson
from onegov.core.collection import GenericCollection
from onegov.core.collection import Pagination
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload


class PaginatedMembershipCollection(GenericCollection, Pagination):

    def __init__(self, session, page=0, agency=None, person=None,
                 updated_gt=None, updated_ge=None, updated_eq=None,
                 updated_le=None, updated_lt=None, exclude_hidden=True):
        super().__init__(session)
        self.page = page
        self.agency = agency
        self.person = person
        # filter keywords
        self.updated_gt = updated_gt
        self.updated_ge = updated_ge
        self.updated_eq = updated_eq
        self.updated_le = updated_le
        self.updated_lt = updated_lt
        # end filter keywords
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
        return self.__class__(
            self.session,
            page=index,
            updated_gt=self.updated_gt,
            updated_ge=self.updated_ge,
            updated_eq=self.updated_eq,
            updated_le=self.updated_le,
            updated_lt=self.updated_lt,
        )

    def for_filter(self, **kwargs):
        return self.__class__(
            session=self.session,
            updated_gt=kwargs.get('updated_gt', self.updated_gt),
            updated_ge=kwargs.get('updated_ge', self.updated_ge),
            updated_eq=kwargs.get('updated_eq', self.updated_eq),
            updated_le=kwargs.get('updated_le', self.updated_le),
            updated_lt=kwargs.get('updated_lt', self.updated_lt),
        )

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

        if self.updated_gt:
            # if 'modified' is not set comparison is done against 'created'
            query = query.filter(
                func.coalesce(
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.modified),
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.created),
                ) > self.updated_gt
            )
        if self.updated_ge:
            query = query.filter(
                func.coalesce(
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.modified),
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.created),
                ) >= self.updated_ge
            )
        if self.updated_eq:
            query = query.filter(
                func.coalesce(
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.modified),
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.created),
                ) == self.updated_eq
            )
        if self.updated_le:
            query = query.filter(
                func.coalesce(
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.modified),
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.created),
                ) <= self.updated_le
            )
        if self.updated_lt:
            query = query.filter(
                func.coalesce(
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.modified),
                    func.date_trunc('minute',
                                    ExtendedAgencyMembership.created),
                ) < self.updated_lt
            )
        return query
