from onegov.ballot.models import Ballot, Vote
from sqlalchemy import cast, desc, extract, Integer


class VoteCollection(object):

    def __init__(self, session, year=None):
        self.session = session
        self.year = year

    def query(self):
        return self.session.query(Vote)

    def for_year(self, year):
        return self.__class__(self.session, year)

    def get_latest(self):
        """ Returns the votes with the latest date. """

        latest_date = self.query().with_entities(Vote.date)
        latest_date = latest_date.order_by(desc(Vote.date))
        latest_date = latest_date.limit(1).first()

        if not latest_date:
            return None
        else:
            return self.by_date(latest_date)

    def get_years(self):
        """ Returns a list of years for which there are votes. """

        query = self.query()
        query = query.with_entities(cast(extract('year', Vote.date), Integer))
        query = query.order_by(desc(Vote.date))

        return list(reversed(sorted((set(r[0] for r in query.all())))))

    def by_date(self, date):
        """ Returns the votes on the given date. """

        query = self.query()
        query = query.filter(Vote.date == date)
        query = query.order_by(Vote.domain, Vote.shortcode, Vote.title)

        return query.all()

    def by_year(self, year=None):
        """ Returns the votes for the current/given year. """

        year = year or self.year

        query = self.query()
        query = query.filter(extract('year', Vote.date) == year)
        query = query.order_by(
            Vote.date, Vote.domain, Vote.shortcode, Vote.title
        )

        return query.all()

    def by_id(self, id):
        """ Returns the vote by id. """

        query = self.query()
        query = query.filter(Vote.id == id)

        return query.first()


class BallotCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Ballot)

    def by_id(self, id):
        return self.query().filter(Ballot.id == id).first()
