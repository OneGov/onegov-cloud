from onegov.ballot import Vote, VoteCollection
from sqlalchemy import asc, desc


class Manage(object):
    """ Provides management methods for votes/elections. """

    orderkeys = {
        'date': Vote.date,
        'title': Vote.title
    }
    directions = {
        'asc': asc,
        'desc': desc
    }

    def __init__(self, session, order_by='date', direction='desc'):
        self.session = session
        self.order_by = self.orderkeys.get(order_by, Vote.date)
        self.direction = self.directions.get(direction, desc)

    @property
    def votes(self):
        query = VoteCollection(self.session).query()
        query = query.order_by(self.direction(self.order_by), Vote.title)

        return query.all()
