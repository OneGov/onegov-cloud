from __future__ import annotations

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from onegov.core.orm import Base
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import UUID


class SearchIndex(Base, UTCPublicationMixin):

    This table contains fullt text search (fts) index information for all
    searchable models, including the owner of the index, the type of the
    owner, and the full-text search data. It is used to facilitate efficient
    searching across different models and entries.

    """

    __tablename__ = 'search_index'

    id = Column(Integer, primary_key=True)

    #: The class name of the original model on the index entry
    owner_type = Column(String, nullable=False)

    #: The int id of the original model if it is an integer
    owner_id_int = Column(Integer, nullable=True)

    #: The uuid id of the original model if it is a uuid
    owner_id_uuid = Column(UUID, nullable=True)

    #: The string id of the original model if it is a string
    owner_id_str = Column(String, nullable=True)

    #: The full text search index data (fts properties)
    fts_idx_data = Column(JSONB, default={})

    #: The postgres full text search (fts) index
    fts_idx = Column(TSVECTOR)

    __mapper_args__ = {
        'polymorphic_on': owner_type
    }
