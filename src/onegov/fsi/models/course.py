from arrow import utcnow
from onegov.core.html import html_to_text
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column, Text, Boolean, Interval, desc
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

    refresh_interval = Column(Interval)

    # If the course has to be refreshed after some interval
    mandatory_refresh = Column(Boolean, nullable=False, default=False)

    # hides the course in the collection for non-admins
    hidden_from_public = Column(Boolean, nullable=False, default=False)

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
