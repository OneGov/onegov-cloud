""" A OneGov Page is an Adjacency List used to represent pages with any kind
of content in a hierarchy.

See also: `<http://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html>`_

"""

from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin, TimestampMixin


class Page(AdjacencyList, ContentMixin, TimestampMixin):
    """ Defines a generic page. """

    __tablename__ = 'pages'
