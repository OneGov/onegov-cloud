from __future__ import annotations

from onegov.core.collection import Pagination
from onegov.election_day.models import ElectionCompound
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


class ElectionCompoundCollection(Pagination[ElectionCompound]):

    page: int

    def __init__(
        self,
        session: Session,
        page: int = 0,
        year: int | None = None
    ):
        super().__init__(page)
        self.session = session
        self.year = year

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self.year == other.year and self.page == other.page

    def subset(self) -> Query[ElectionCompound]:
        query = self.query()
        query = query.order_by(
            desc(ElectionCompound.date),
            ElectionCompound.shortcode,
            ElectionCompound.title
        )
        if self.year:
            query = query.filter(
                extract('year', ElectionCompound.date) == self.year
            )

        return query

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index, self.year)

    def for_year(self, year: int | None) -> Self:
        return self.__class__(self.session, 0, year)

    def query(self) -> Query[ElectionCompound]:
        return self.session.query(ElectionCompound)

    def get_latest(self) -> list[ElectionCompound] | None:
        """ Returns the election compounds with the latest date. """

        latest_date = self.query().with_entities(ElectionCompound.date)
        latest_date = latest_date.order_by(desc(ElectionCompound.date))
        latest_date = latest_date.limit(1).scalar()
        return self.by_date(latest_date) if latest_date else None

    def get_years(self) -> list[int]:
        """ Returns a list of years for which there are election compounds.

        """

        year = cast(extract('year', ElectionCompound.date), Integer)
        query = self.session.query(distinct(year))
        query = query.order_by(desc(year))

        return [year for year, in query]

    def by_date(self, date: date) -> list[ElectionCompound]:
        """ Returns the election compounds on the given date. """

        query = self.query()
        query = query.filter(ElectionCompound.date == date)
        query = query.order_by(
            ElectionCompound.shortcode,
            ElectionCompound.title
        )

        return query.all()

    def by_year(self, year: int | None = None) -> list[ElectionCompound]:
        """ Returns the election compounds for the current/given year. """

        year = year or self.year

        query = self.query()
        query = query.filter(extract('year', ElectionCompound.date) == year)
        query = query.order_by(
            ElectionCompound.date,
            ElectionCompound.shortcode,
            ElectionCompound.title
        )

        return query.all()

    def by_id(self, id: str) -> ElectionCompound | None:
        """ Returns the election compound by id. """

        query = self.query()
        query = query.filter(ElectionCompound.id == id)

        return query.first()
