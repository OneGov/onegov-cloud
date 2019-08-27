from sqlalchemy_utils import QueryChain as QueryChainBase


class QueryChain(QueryChainBase):
    """ Extends SQLAlchemy Utils' QueryChain with some extra methods. """

    def slice(self, start, end):
        return self[start:end]

    def first(self):
        return next((o for o in self), None)

    def all(self):
        return tuple(self)
