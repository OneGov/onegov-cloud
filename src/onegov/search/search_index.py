from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import UUID, UTCDateTime
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.dialects.postgresql import ARRAY, HSTORE, JSONB, TSVECTOR
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
    owner_type = Column(String, nullable=False, index=True)

    #: Table name of the original model associated with the index entry
    owner_tablename = Column(String, nullable=False, index=True)

    #: Integer id of the original model if applicable
    owner_id_int = Column(Integer, nullable=True)

    #: UUID id of the original model if applicable
    owner_id_uuid = Column(UUID, nullable=True)

    #: String id of the original model if applicable
    owner_id_str = Column(String, nullable=True)

    #: Indicates if entry is public (Searchable::es_public)
    public = Column(Boolean, nullable=False, default=False)

    #: Access level of entry (AccessExtension::access)
    access = Column(String, nullable=False, default='public', index=True)

    #: Timestamp of the last change to the entry (Searchable::es_last_change)
    last_change = Column(UTCDateTime, nullable=False, index=True)

    #: Tags associated with the entry (Searchable::es_tags)
    _tags: Column[dict[str, str] | None] = Column(  # type:ignore
        MutableDict.as_mutable(HSTORE),  # type:ignore[no-untyped-call]
        nullable=True,
        name='tags'
    )

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
        # unique partial indeces for ensuring we have no duplicates
        # NOTE: If we lift our minimum Postgres version to 15 we
        #       can replace this with a single unique constraint
        #       using NULLS NOT DISTINCT, but we may still want
        #       partial indeces in addition to the shared unique index
        Index(
            'uq_search_index_owner_tablename_id_int',
            owner_tablename,
            owner_id_int,
            unique=True,
            postgresql_where=owner_id_int.isnot(None)
        ),
        Index(
            'uq_search_index_owner_tablename_id_uuid',
            owner_tablename,
            owner_id_uuid,
            unique=True,
            postgresql_where=owner_id_uuid.isnot(None),
        ),
        Index(
            'uq_search_index_owner_tablename_id_str',
            owner_tablename,
            owner_id_str,
            unique=True,
            postgresql_where=owner_id_str.isnot(None),
        ),
        # avoid more than one owner_id being set per row
        CheckConstraint(
            """
                (
                        owner_id_int IS NOT NULL
                    AND owner_id_uuid IS NULL
                    AND owner_id_str IS NULL
                ) OR (
                        owner_id_int IS NULL
                    AND owner_id_uuid IS NOT NULL
                    AND owner_id_str IS NULL
                ) OR (
                        owner_id_int IS NULL
                    AND owner_id_uuid IS NULL
                    AND owner_id_str IS NOT NULL
                )
            """,
            'ck_search_index_exactly_one_owner_id_set',
        ),
        # partial compound indeces for owner type lookups
        Index(
            'ix_search_index_owner_type_id_int',
            owner_type,
            owner_id_int,
            postgresql_where=owner_id_int.isnot(None)
        ),
        Index(
            'ix_search_index_owner_type_id_uuid',
            owner_type,
            owner_id_uuid,
            postgresql_where=owner_id_uuid.isnot(None),
        ),
        Index(
            'ix_search_index_owner_type_id_str',
            owner_type,
            owner_id_str,
            postgresql_where=owner_id_str.isnot(None),
        ),
        # compound index for public and access lookups
        Index(
            'ix_search_index_public_access',
            public,
            access
        ),
        # gin indeces for complex types
        Index(
            'ix_search_index_tags',
            _tags,
            postgresql_using='gin'
        ),
        Index(
            'ix_search_index_suggestion',
            suggestion,
            postgresql_using='gin'
        ),
        Index(
            'ix_search_index_fts_idx_data',
            fts_idx_data,
            postgresql_using='gin',
            postgresql_ops={'fts_idx_data': 'jsonb_ops'},
        ),
        Index(
            'ix_search_index_fts_idx',
            fts_idx,
            postgresql_using='gin'
        ),
    )

    @property
    def tags(self) -> set[str]:
        return set(self._tags.keys()) if self._tags else set()

    @tags.setter
    def tags(self, value: Iterable[str]) -> None:
        self._tags = dict.fromkeys(value, '') if value else {}
