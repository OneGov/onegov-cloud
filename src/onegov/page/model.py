""" A OneGov Page is an Adjacency List used to represent pages with any kind
of content in a hierarchy.

See also: `<https://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html>`_

"""
from sqlalchemy import func
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.hybrid import hybrid_property

from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin


class Page(AdjacencyList, ContentMixin, TimestampMixin, UTCPublicationMixin):
    """ Defines a generic page. """

    __tablename__ = 'pages'

    # column for full text search index
    fts_idx = Column(TSVECTOR)

    @property
    def search_score(self):
        return 1

    @hybrid_property
    def published_or_created(self):
        return self.publication_start or self.created

    @published_or_created.expression  # type:ignore[no-redef]
    def published_or_created(self):
        return func.coalesce(Page.publication_start, Page.created)

    @property
    def es_public(self):
        return self.access == 'public' and self.published
