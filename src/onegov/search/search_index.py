from __future__ import annotations

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from onegov.core.orm import Base
from onegov.core.orm.types import UUID


class SearchIndex(Base):
    """ Full Text Search Index (fts) for all searchable models and entries.

    This table contains index information for all searchable models,
    including the owner of the index, the type of the owner, and the
    full-text search data. It is used to facilitate efficient searching
    across different models and entries.

    """

    __tablename__ = 'search_index'

    id = Column(Integer, primary_key=True)

    owner_type = Column(String, nullable=False)

    owner_id_int = Column(Integer, nullable=True)

    owner_id_uuid = Column(UUID, nullable=True)

    owner_id_str = Column(String, nullable=True)

    fts_idx_data = Column(JSONB, default={})

    fts_idx = Column(TSVECTOR)

    __mapper_args__ = {
        'polymorphic_on': owner_type
    }
