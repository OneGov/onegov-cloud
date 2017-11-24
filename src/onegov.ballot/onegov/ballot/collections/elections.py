from onegov.ballot.models import Election
from onegov.core.collection import Pagination
from sqlalchemy import cast
from sqlalchemy import desc
from sqlalchemy import distinct
from sqlalchemy import extract
from sqlalchemy import Integer


class ElectionCollectionPagination(Pagination):

    def __init__(self, session, page=0, year=None):
        self.session = session
        self.page = page
        self.year = year

    def __eq__(self, other):
        return self.year == other.year and self.page == other.page

    def subset(self):
        query = self.query()
        query = query.order_by(
            desc(Election.date), Election.shortcode, Election.title
        )
        if self.year:
            query = query.filter(extract('year', Election.date) == self.year)

        return query

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index, self.year)

    def for_year(self, year):
        return self.__class__(self.session, 0, year)


class ElectionCollection(ElectionCollectionPagination):

    def query(self):
        return self.session.query(Election)

    def get_latest(self):
        """ Returns the elections with the latest date. """

        latest_date = self.query().with_entities(Election.date)
        latest_date = latest_date.order_by(desc(Election.date))
        latest_date = latest_date.limit(1).first()

        if not latest_date:
            return None
        else:
            return self.by_date(latest_date)

    def get_years(self):
        """ Returns a list of years for which there are elections. """

        year = cast(extract('year', Election.date), Integer)
        query = self.session.query
        query = query(distinct(year))
        query = query.order_by(
            desc(year)
        )

        return list(r[0] for r in query.all())

    def by_date(self, date):
        """ Returns the elections on the given date. """

        query = self.query()
        query = query.filter(Election.date == date)
        query = query.order_by(
            Election.domain, Election.shortcode, Election.title
        )

        return query.all()

    def by_year(self, year=None):
        """ Returns the elections for the current/given year. """

        year = year or self.year

        query = self.query()
        query = query.filter(extract('year', Election.date) == year)
        query = query.order_by(
            Election.date, Election.domain, Election.shortcode, Election.title
        )

        return query.all()

    def by_id(self, id):
        """ Returns the election by id. """

        query = self.query()
        query = query.filter(Election.id == id)

        return query.first()
