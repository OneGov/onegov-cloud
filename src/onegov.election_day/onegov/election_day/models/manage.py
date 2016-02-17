from onegov.ballot import Election, ElectionCollection
from onegov.ballot import Vote, VoteCollection
from sqlalchemy import asc, desc


class Manage(object):
    """ Provides management methods for votes/elections. """

    orderkeys = {
        'date': {
            'election': Election.date,
            'vote': Vote.date
        },
        'title': {
            'election': Election.title,
            'vote': Vote.title
        }
    }
    directions = {
        'asc': asc,
        'desc': desc
    }

    def __init__(self, session, order_by='date', direction='desc'):
        self.session = session
        self.order_by = self.orderkeys.get(order_by, 'date')
        self.direction = self.directions.get(direction, desc)

    @property
    def elections(self):
        query = ElectionCollection(self.session).query()
        query = query.order_by(
            self.direction(self.order_by['election']), Election.title
        )

        return query.all()

    @property
    def votes(self):
        query = VoteCollection(self.session).query()
        query = query.order_by(
            self.direction(self.order_by['vote']), Vote.title
        )

        return query.all()
