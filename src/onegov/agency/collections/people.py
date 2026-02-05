from __future__ import annotations

from functools import cached_property

from onegov.agency.models import ExtendedPerson
from onegov.agency.utils import filter_modified_or_created
from onegov.core.collection import Pagination
from onegov.people import Agency
from onegov.people import AgencyMembership
from onegov.people.collections.people import BasePersonCollection
from sqlalchemy import func
from sqlalchemy import or_


from typing import Self
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import TypedDict
    from typing_extensions import Unpack

    class FilterParams(TypedDict, total=False):
        letter: str | None
        agency: str | None
        first_name: str | None
        last_name: str | None
        updated_gt: datetime | str | None
        updated_ge: datetime | str | None
        updated_eq: datetime | str | None
        updated_le: datetime | str | None
        updated_lt: datetime | str | None


class ExtendedPersonCollection(
    BasePersonCollection[ExtendedPerson],
    Pagination[ExtendedPerson]
):
    """ Extends the common person collection by the ability to filter by
    the first letter of the last name, by the organization, by first or last
    name. Adds pagination.

    """

    batch_size = 20

    @property
    def model_class(self) -> type[ExtendedPerson]:
        return ExtendedPerson

    def __init__(
        self,
        session: Session,
        page: int = 0,
        letter: str | None = None,
        agency: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        updated_gt: datetime | str | None = None,
        updated_ge: datetime | str | None = None,
        updated_eq: datetime | str | None = None,
        updated_le: datetime | str | None = None,
        updated_lt: datetime | str | None = None,
        xlsx_modified: str | None = None
    ) -> None:

        self.session = session
        self.page = page

        # filter keywords
        self.letter = letter.upper() if letter else None
        self.agency = agency
        self.first_name = first_name
        self.last_name = last_name
        self.updated_gt = updated_gt
        self.updated_ge = updated_ge
        self.updated_eq = updated_eq
        self.updated_le = updated_le
        self.updated_lt = updated_lt
        # end filter keywords

        self.exclude_hidden = False
        # Usage for link generation of people excel based on timestamp
        self.xlsx_modified = xlsx_modified

    def subset(self) -> Query[ExtendedPerson]:
        return self.query()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.letter == other.letter
            and self.agency == other.agency
        )

    def page_by_index(self, page: int) -> Self:
        return self.__class__(
            self.session,
            page=page,
            letter=self.letter,
            agency=self.agency,
            first_name=self.first_name,
            last_name=self.last_name,
            updated_gt=self.updated_gt,
            updated_ge=self.updated_ge,
            updated_eq=self.updated_eq,
            updated_le=self.updated_le,
            updated_lt=self.updated_lt,
        )

    def for_filter(self, **kwargs: Unpack[FilterParams]) -> Self:
        return self.__class__(
            session=self.session,
            letter=kwargs.get('letter', self.letter),
            agency=kwargs.get('agency', self.agency),
            first_name=kwargs.get('first_name', self.first_name),
            last_name=kwargs.get('last_name', self.last_name),
            updated_gt=kwargs.get('updated_gt', self.updated_gt),
            updated_ge=kwargs.get('updated_ge', self.updated_ge),
            updated_eq=kwargs.get('updated_eq', self.updated_eq),
            updated_le=kwargs.get('updated_le', self.updated_le),
            updated_lt=kwargs.get('updated_lt', self.updated_lt),
        )

    def query(self) -> Query[ExtendedPerson]:
        query = self.session.query(ExtendedPerson)
        if self.exclude_hidden:
            query = query.filter(
                or_(
                    ExtendedPerson.meta['access'] == 'public',
                    ExtendedPerson.meta['access'] == None,
                ),
                ExtendedPerson.published.is_(True)
            )
        if self.letter:
            query = query.filter(
                func.upper(
                    func.unaccent(ExtendedPerson.last_name)
                ).startswith(self.letter)
            )
        if self.agency:
            query = query.join(ExtendedPerson.memberships)
            query = query.join(AgencyMembership.agency)
            query = query.filter(Agency.title == self.agency)
        if self.first_name:
            query = query.filter(
                func.lower(
                    func.unaccent(ExtendedPerson.first_name)
                ) == self.first_name.lower()
            )
        if self.last_name:
            query = query.filter(
                func.lower(
                    func.unaccent(ExtendedPerson.last_name)
                ) == self.last_name.lower()
            )
        if self.updated_gt:
            query = filter_modified_or_created(query, '>', self.updated_gt,
                                               ExtendedPerson)
        if self.updated_ge:
            query = filter_modified_or_created(query, '>=', self.updated_ge,
                                               ExtendedPerson)
        if self.updated_eq:
            query = filter_modified_or_created(query, '==', self.updated_eq,
                                               ExtendedPerson)
        if self.updated_le:
            query = filter_modified_or_created(query, '<=', self.updated_le,
                                               ExtendedPerson)
        if self.updated_lt:
            query = filter_modified_or_created(query, '<', self.updated_lt,
                                               ExtendedPerson)
        query = query.order_by(
            func.upper(func.unaccent(ExtendedPerson.last_name)),
            func.upper(func.unaccent(ExtendedPerson.first_name))
        )
        return query

    @cached_property
    def used_letters(self) -> list[str]:
        """ Returns a list of all the distinct first letters of people's
        last names.

        """
        letter = func.left(ExtendedPerson.last_name, 1)
        letter = func.upper(func.unaccent(letter))
        query = self.session.query(letter.distinct().label('letter'))
        query = query.order_by(letter)
        return [letter for letter, in query]

    @cached_property
    def used_agencies(self) -> list[str]:
        """ Returns a list of all the agencies people are members of.

        """
        query = self.session.query(Agency.title)
        query = query.filter(Agency.memberships.any())
        query = query.order_by(func.upper(func.unaccent(Agency.title)))
        return [title for title, in query]
