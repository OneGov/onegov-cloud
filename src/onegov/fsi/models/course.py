from arrow import utcnow
from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.html import html_to_text
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable, Searchable
from sqlalchemy import Column, Text, Boolean, Integer, Index
from sqlalchemy import Computed  # type:ignore[attr-defined]
from sqlalchemy.ext.hybrid import hybrid_property
from uuid import uuid4


class Course(Base, ORMSearchable):
    __tablename__ = 'fsi_courses'

    es_properties = {
        'name': {'type': 'localized'},
        'description': {'type': 'localized'},
    }
    es_public = True

    id = Column(UUID, primary_key=True, default=uuid4)

    name = Column(Text, nullable=False, unique=True)

    description = Column(Text, nullable=False)

    # saved as integer (years), accessed as years
    refresh_interval = Column(Integer)

    # If the course has to be refreshed after some interval
    mandatory_refresh = Column(Boolean, nullable=False, default=False)

    # hides the course in the collection for non-admins
    hidden_from_public = Column(Boolean, nullable=False, default=False)

    fts_idx = Column(TSVECTOR, Computed('', persisted=True))

    __table_args__ = (
        Index('fts_idx', fts_idx, postgresql_using='gin'),
    )

    @property
    def search_score(self):
        return 2

    @staticmethod
    def psql_tsvector_string():
        """
        index is built on columns name and description
        """
        return Searchable.create_tsvector_string('name', 'description')

    @property
    def title(self):
        return self.name

    @property
    def lead(self):
        text = html_to_text(self.description)

        if len(text) > 160:
            return text[:160] + '…'
        else:
            return text

    @property
    def description_html(self):
        """
        Returns the description that is saved as HTML from the redactor js
        plugin.
        """
        return self.description

    @hybrid_property
    def future_events(self):
        from onegov.fsi.models import CourseEvent
        return self.events.filter(CourseEvent.start > utcnow()).order_by(
            CourseEvent.start)
