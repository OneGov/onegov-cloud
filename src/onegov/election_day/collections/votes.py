from __future__ import annotations

from onegov.core.collection import Pagination
from onegov.election_day.models import Vote
from sqlalchemy import cast
from sqlalchemy import desc
from sqlalchemy import distinct
from sqlalchemy import extract
from sqlalchemy import Integer


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from sqlalchemy.orm import Query, Session
    from typing import Self


class VoteCollection(Pagination[Vote]):

    page: int

    def __init__(
        self,
        session: Session,
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

    def subset(self) -> Query[Vote]:
        query = self.query()
        query = query.order_by(desc(Vote.date), Vote.shortcode, Vote.title)
        if self.year:
            query = query.filter(extract('year', Vote.date) == self.year)

        return query

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index, self.year)

    def for_year(self, year: int | None) -> Self:
        return self.__class__(self.session, 0, year)

    def query(self) -> Query[Vote]:
        return self.session.query(Vote)

    def get_latest(self) -> list[Vote] | None:
        """ Returns the votes with the latest date. """

        latest_date = self.query().with_entities(Vote.date)
        latest_date = latest_date.order_by(desc(Vote.date))
        latest_date = latest_date.limit(1).scalar()
        return self.by_date(latest_date) if latest_date else None

    def get_years(self) -> list[int]:
        """ Returns a list of years for which there are votes. """

        year = cast(extract('year', Vote.date), Integer)
        query = self.session.query(distinct(year))
        query = query.order_by(desc(year))

        return [year for year, in query]

    def by_date(self, date: date) -> list[Vote]:
        """ Returns the votes on the given date. """

        query = self.query()
        query = query.filter(Vote.date == date)
        query = query.order_by(Vote.domain, Vote.shortcode, Vote.title)

        return query.all()

    def by_year(self, year: int | None = None) -> list[Vote]:
        """ Returns the votes for the current/given year. """

        year = year or self.year

        query = self.query()
        query = query.filter(extract('year', Vote.date) == year)
        query = query.order_by(
            Vote.date, Vote.domain, Vote.shortcode, Vote.title
        )

        return query.all()

    def by_id(self, id: str) -> Vote | None:
        """ Returns the vote by id. """

        query = self.query()
        query = query.filter(Vote.id == id)

        return query.first()
