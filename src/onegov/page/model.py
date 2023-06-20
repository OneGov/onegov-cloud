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
from onegov.search.utils import create_tsvector_string, adds_fts_column, \
    drops_fts_column


FTS_PAGE_IDX_COL_NAME = 'fts_page_idx'


def page_tsvector_string():
    """
    index is built on column title as well as on the json
    fields lead and text in content column if not NULL
    """
    s = create_tsvector_string('title')
    s += " || ' ' || coalesce(((content ->> 'lead')), '')"
    s += " || ' ' || coalesce(((content ->> 'text')), '')"
    return s


class Page(AdjacencyList, ContentMixin, TimestampMixin, UTCPublicationMixin):
    """ Defines a generic page. """

    __tablename__ = 'pages'

    # column for full text search index
    fts_pages_idx = Column(TSVECTOR, Computed(
        f"to_tsvector('german', {page_tsvector_string()})",
        persisted=True))

    __table_args__ = (
        Index(
            'fts_events',
            fts_pages_idx,
            postgresql_using='gin'
        ),
    )

    @hybrid_property
    def published_or_created(self):
        return self.publication_start or self.created

    @published_or_created.expression  # type:ignore[no-redef]
    def published_or_created(self):
        return func.coalesce(Page.publication_start, Page.created)

    @property
    def es_public(self):
        return self.access == 'public' and self.published

    @staticmethod
    def reindex(session, schema):
        """
        Re-indexes the table by dropping and adding the full text search
        column.
        """
        Page.drop_fts_column(session, schema)
        Page.add_fts_column(session, schema)

    @staticmethod
    def add_fts_column(session, schema):
        """
        Adds full text search column to table `events`

        :param session: db session
        :param schema: schema the full text column shall be added
        :return: None
        """
        adds_fts_column(schema, session, Page.__tablename__,
                        FTS_PAGE_IDX_COL_NAME, page_tsvector_string())

    @staticmethod
    def drop_fts_column(session, schema):
        """
        Drops the full text search column

        :param session: db session
        :param schema: schema the full text column shall be added
        :return: None
        """
        drops_fts_column(schema, session, Page.__tablename__,
                         FTS_PAGE_IDX_COL_NAME)
