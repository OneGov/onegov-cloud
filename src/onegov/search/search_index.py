from __future__ import annotations

from datetime import datetime
from uuid import UUID
from onegov.core.orm import Base
from onegov.core.orm.mixins import UTCPublicationMixin
from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import mapped_column, Mapped


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

    id: Mapped[int] = mapped_column(primary_key=True)

    #: Class name of the original model associated with the index entry
    owner_type: Mapped[str] = mapped_column(String, index=True)

    #: Table name of the original model associated with the index entry
    owner_tablename: Mapped[str] = mapped_column(String, index=True)

    #: Integer id of the original model if applicable
    owner_id_int: Mapped[int | None] = mapped_column()

    #: UUID id of the original model if applicable
    owner_id_uuid: Mapped[UUID | None] = mapped_column()

    #: String id of the original model if applicable
    owner_id_str: Mapped[str | None] = mapped_column(String)

    #: Indicates if entry is public (Searchable::fts_public)
    public: Mapped[bool] = mapped_column(default=False)

    #: Access level of entry (AccessExtension::access)
    access: Mapped[str] = mapped_column(String, default='public', index=True)

    # FIXME: This might be a bit of a misnomer now, or we want to split this
    #        into two separate columns. This is more of a reference date for
    #        when this entry is relevant. So it affectes time-based search
    #        and time-based relevance.
    #: Timestamp of the last change to the entry (Searchable::fts_last_change)
    last_change: Mapped[datetime | None] = mapped_column(index=True)

    #: Tags associated with the entry (Searchable::fts_tags)
    _tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        name='tags',
    )

    #: Suggestions for search functionality (Searchable::fts_suggestion)
    suggestion: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    #: Postgres full-text search (fts) index (title)
    title_vector: Mapped[str] = mapped_column(TSVECTOR)

    #: Postgres full-text search (fts) index (data)
    data_vector: Mapped[str] = mapped_column(TSVECTOR)

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
            postgresql_where=owner_id_int.is_not(None)
        ),
        Index(
            'uq_search_index_owner_tablename_id_uuid',
            owner_tablename,
            owner_id_uuid,
            unique=True,
            postgresql_where=owner_id_uuid.is_not(None),
        ),
        Index(
            'uq_search_index_owner_tablename_id_str',
            owner_tablename,
            owner_id_str,
            unique=True,
            postgresql_where=owner_id_str.is_not(None),
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
            postgresql_where=owner_id_int.is_not(None)
        ),
        Index(
            'ix_search_index_owner_type_id_uuid',
            owner_type,
            owner_id_uuid,
            postgresql_where=owner_id_uuid.is_not(None),
        ),
        Index(
            'ix_search_index_owner_type_id_str',
            owner_type,
            owner_id_str,
            postgresql_where=owner_id_str.is_not(None),
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
            'ix_search_index_title_vector',
            title_vector,
            postgresql_using='gin'
        ),
        Index(
            'ix_search_index_data_vector',
            data_vector,
            postgresql_using='gin'
        ),
    )

    @property
    def tags(self) -> set[str]:
        return set(self._tags) if self._tags else set()

    @tags.setter
    def tags(self, value: Iterable[str]) -> None:
        # FIXME: Do we care about duplicates?
        self._tags = list(value) if value else []
