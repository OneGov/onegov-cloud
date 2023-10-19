from onegov.ballot.models import Election
from onegov.core.collection import Pagination
from sqlalchemy import cast
from sqlalchemy import desc
from sqlalchemy import distinct
from sqlalchemy import extract
from sqlalchemy import Integer


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from sqlalchemy.orm import Query, Session
    from typing_extensions import Self
    from uuid import UUID


# FIXME: Why is this split into two classes? So it can be generic?
class ElectionCollectionPagination(Pagination[Election]):

    def __init__(
        self,
        session: 'Session',
        page: int = 0,
        year: int | None = None
    ):
        self.session = session
        self.page = page
        self.year = year

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.year == other.year and self.page == other.page

    def subset(self) -> 'Query[Election]':
        query = self.query()  # type:ignore[attr-defined]
        query = query.order_by(
            desc(Election.date), Election.shortcode, Election.title
        )
        if self.year:
            query = query.filter(extract('year', Election.date) == self.year)

        return query

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> 'Self':
        return self.__class__(self.session, index, self.year)

    def for_year(self, year: int) -> 'Self':
        return self.__class__(self.session, 0, year)


class ElectionCollection(ElectionCollectionPagination):

    def query(self) -> 'Query[Election]':
        return self.session.query(Election)

    def get_latest(self) -> list[Election] | None:
        """ Returns the elections with the latest date. """

        latest_date = self.query().with_entities(Election.date)
        latest_date = latest_date.order_by(desc(Election.date))
        latest_date = latest_date.limit(1).scalar()
        return self.by_date(latest_date) if latest_date else None

    def get_years(self) -> list[int]:
        """ Returns a list of years for which there are elections. """

        year = cast(extract('year', Election.date), Integer)
        query = self.session.query(distinct(year))
        query = query.order_by(
            desc(year)
        )

        return [year for year, in query]

    def by_date(self, date: 'date') -> list[Election]:
        """ Returns the elections on the given date. """

        query = self.query()
        query = query.filter(Election.date == date)
        query = query.order_by(
            Election.domain, Election.shortcode, Election.title
        )

        return query.all()

    def by_year(self, year: int | None = None) -> list[Election]:
        """ Returns the elections for the current/given year. """

        year = year or self.year

        query = self.query()
        query = query.filter(extract('year', Election.date) == year)
        query = query.order_by(
            Election.date, Election.domain, Election.shortcode, Election.title
        )

        return query.all()

    def by_id(self, id: 'UUID') -> Election | None:
        """ Returns the election by id. """

        query = self.query()
        query = query.filter(Election.id == id)

        return query.first()
