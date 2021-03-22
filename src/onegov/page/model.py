""" A OneGov Page is an Adjacency List used to represent pages with any kind
of content in a hierarchy.

See also: `<http://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html>`_

"""
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.form.mixins import UTCPublicationMixin


class Page(AdjacencyList, ContentMixin, TimestampMixin, UTCPublicationMixin):
    """ Defines a generic page. """

    __tablename__ = 'pages'

    @hybrid_property
    def published_or_created(self):
        return self.publication_start or self.created

    @published_or_created.expression
    def published_or_created(self):
        return func.coalesce(Page.publication_start, Page.created)
