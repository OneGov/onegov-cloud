from __future__ import annotations

from sqlalchemy import Column, Integer, String, Boolean, Index
from sqlalchemy.dialects.postgresql import ARRAY, HSTORE, JSONB, TSVECTOR

from onegov.core.orm import Base
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import UUID, UTCDateTime
from sqlalchemy.ext.mutable import MutableDict


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


class SearchIndex(Base, UTCPublicationMixin):
    """Full-text Search Index (fts) for all searchable models and entries.

    This table contains full-text search (fts) index information for all
    searchable models, including the owner of the index, the type of the
    owner, and the full-text search data. It is used to facilitate efficient
    searching across different models and entries.

    """

    __tablename__ = 'search_index'

    id = Column(Integer, primary_key=True)

    #: Class name of the original model associated with the index entry
    owner_type = Column(String, nullable=False)

    #: Integer id of the original model if applicable
    owner_id_int = Column(Integer, nullable=True)

    #: UUID id of the original model if applicable
    owner_id_uuid = Column(UUID, nullable=True)

    #: String id of the original model if applicable
    owner_id_str = Column(String, nullable=True)

    #: Indicates if entry is public (Searchable::es_public)
    public = Column(Boolean, nullable=False, default=False)

    #: Access level of entry (AccessExtension::access)
    access = Column(String, nullable=False, default='public')

    #: Timestamp of the last change to the entry (Searchable::es_last_change)
    last_change = Column(UTCDateTime, nullable=False)

    #: Tags associated with the entry (Searchable::es_tags)
    _tags = Column(MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    #: Suggestions for search functionality (Searchable::es_suggestion)
    suggestion = Column(ARRAY(String), nullable=True)

    #: Full-text search index data (fts properties)
    fts_idx_data = Column(JSONB, default={})

    #: Postgres full-text search (fts) index
    fts_idx = Column(TSVECTOR)

    __mapper_args__ = {
        'polymorphic_on': owner_type
    }

    __table_args__ = (
        Index('ix_search_index_owner_type', 'owner_type'),
        Index('ix_search_index_owner_id_int', 'owner_id_int'),
        Index('ix_search_index_owner_id_uuid', 'owner_id_uuid'),
        Index('ix_search_index_owner_id_str', 'owner_id_str'),
        Index('ix_search_index_public', 'public'),
        Index('ix_search_index_access', 'access'),
        Index('ix_search_index_last_change', 'last_change'),
        Index('ix_search_index_tags', 'tags'),
        Index('ix_search_index_suggestion', 'suggestion'),
        Index('ix_search_index_fts_idx_data', 'fts_idx_data'),
        Index('ix_search_index_fts_idx', 'fts_idx'),
    )

    @property
    def tags(self) -> set[str]:
        return set(self._tags.keys()) if self._tags else set()

    # FIXME: asymmetric property
    @tags.setter
    def tags(self, value: Iterable[str]) -> None:
        self._tags = dict.fromkeys(value, '') if value else {}
