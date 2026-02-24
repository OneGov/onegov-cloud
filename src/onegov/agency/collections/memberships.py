from __future__ import annotations

from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import ExtendedPerson
from onegov.agency.utils import filter_modified_or_created
from onegov.core.collection import GenericCollection
from onegov.core.collection import Pagination
from sqlalchemy import or_
from sqlalchemy.orm import joinedload


from typing import Self
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import TypedDict
    from typing_extensions import Unpack

    class FilterParams(TypedDict, total=False):
        updated_gt: datetime | str | None
        updated_ge: datetime | str | None
        updated_eq: datetime | str | None
        updated_le: datetime | str | None
        updated_lt: datetime | str | None


class PaginatedMembershipCollection(
    GenericCollection[ExtendedAgencyMembership],
    Pagination[ExtendedAgencyMembership]
):

    def __init__(
        self,
        session: Session,
        page: int = 0,
        agency: str | None = None,
        person: str | None = None,
        updated_gt: datetime | str | None = None,
        updated_ge: datetime | str | None = None,
        updated_eq: datetime | str | None = None,
        updated_le: datetime | str | None = None,
        updated_lt: datetime | str | None = None,
        exclude_hidden: bool = True
    ) -> None:
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
    def model_class(self) -> type[ExtendedAgencyMembership]:
        return ExtendedAgencyMembership

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and other.page == self.page
            and other.agency == self.agency
            and other.person == self.person
        )

    def subset(self) -> Query[ExtendedAgencyMembership]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            updated_gt=self.updated_gt,
            updated_ge=self.updated_ge,
            updated_eq=self.updated_eq,
            updated_le=self.updated_le,
            updated_lt=self.updated_lt,
        )

    def for_filter(self, **kwargs: Unpack[FilterParams]) -> Self:
        return self.__class__(
            session=self.session,
            updated_gt=kwargs.get('updated_gt', self.updated_gt),
            updated_ge=kwargs.get('updated_ge', self.updated_ge),
            updated_eq=kwargs.get('updated_eq', self.updated_eq),
            updated_le=kwargs.get('updated_le', self.updated_le),
            updated_lt=kwargs.get('updated_lt', self.updated_lt),
        )

    def query(self) -> Query[ExtendedAgencyMembership]:
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
            query = filter_modified_or_created(query, '>', self.updated_gt,
                                               ExtendedAgencyMembership)
        if self.updated_ge:
            query = filter_modified_or_created(query, '>=', self.updated_ge,
                                               ExtendedAgencyMembership)
        if self.updated_eq:
            query = filter_modified_or_created(query, '==', self.updated_eq,
                                               ExtendedAgencyMembership)
        if self.updated_le:
            query = filter_modified_or_created(query, '<=', self.updated_le,
                                               ExtendedAgencyMembership)
        if self.updated_lt:
            query = filter_modified_or_created(query, '<', self.updated_lt,
                                               ExtendedAgencyMembership)
        if self.updated_lt:
            query = filter_modified_or_created(query, '<', self.updated_lt,
                                               ExtendedAgencyMembership)
        return query
