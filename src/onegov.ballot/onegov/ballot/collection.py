from onegov.ballot.models import Vote
from sqlalchemy import desc


class VoteCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Vote)

    def get_latest(self):
        """ Returns the votes with the latest date. """

        latest_date = self.query().with_entities(Vote.date)
        latest_date = latest_date.order_by(desc(Vote.date))
        latest_date = latest_date.limit(1).first()

        if not latest_date:
            return None
        else:
            return self.by_date(latest_date)

    def by_date(self, date):
        """ Returns the votes on the given date. """

        query = self.query()
        query = query.filter(Vote.date == date)
        query = query.order_by(Vote.domain, Vote.id)

        return query.all()

    def by_id(self, id):
        """ Returns the vote by id. """

        query = self.query()
        query = query.filter(Vote.id == id)

        return query.first()
