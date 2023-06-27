""" A OneGov Page is an Adjacency List used to represent pages with any kind
of content in a hierarchy.

See also: `<https://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html>`_

"""
from sqlalchemy import func, Index
from sqlalchemy import Computed  # type:ignore[attr-defined]
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.hybrid import hybrid_property

from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.search import Searchable


class Page(AdjacencyList, ContentMixin, TimestampMixin, UTCPublicationMixin):
    """ Defines a generic page. """

    __tablename__ = 'pages'

    # column for full text search index
    fts_idx = Column(TSVECTOR, Computed('', persisted=True))

    __table_args__ = (
        Index('fts_idx', fts_idx, postgresql_using='gin'),
    )

    @property
    def search_score(self):
        return 1

    @staticmethod
    def psql_tsvector_string():
        """
        index is built on column title as well as on the json
        fields lead and text in content column if not NULL
        """
        s = Searchable.create_tsvector_string('title')
        s += " || ' ' || coalesce(((content ->> 'lead')), '')"
        s += " || ' ' || coalesce(((content ->> 'text')), '')"
        return s

    @hybrid_property
    def published_or_created(self):
        return self.publication_start or self.created

    @published_or_created.expression  # type:ignore[no-redef]
    def published_or_created(self):
        return func.coalesce(Page.publication_start, Page.created)

    @property
    def es_public(self):
        return self.access == 'public' and self.published
