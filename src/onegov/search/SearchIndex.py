from uuid import UUID

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy_utils import UUIDType

from onegov.core.orm import Base


class SearchIndex(Base):

    __tablename__ = 'search_index'

    id = Column(Integer, primary_key=True)
    owner_id = Column(UUIDType(binary=False), nullable=False)
    owner_type = Column(String, nullable=False)
    fts_idx_data = Column(JSONB, default={})
    fts_idx = Column(TSVECTOR)

    @property
    def owner(self):
        # This should return the actual owner object based on the owner_id
        # and owner_type
        if not self.owner_type or not self.owner_id:
            return None

        return self.session.query(self.owner_type).get(self.owner_id)
