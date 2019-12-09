from uuid import uuid4

from arrow import utcnow
from sqlalchemy import Column, Text, Boolean, Interval
from sqlalchemy.ext.hybrid import hybrid_property

from onegov.core.orm import Base
from onegov.core.orm.types import UUID


class Course(Base):
    __tablename__ = 'fsi_courses'

    id = Column(UUID, primary_key=True, default=uuid4)

    name = Column(Text, nullable=False, unique=True)
    # Long description
    description = Column(Text, nullable=False)

    refresh_interval = Column(Interval)

    # If the course has to be refreshed after some interval
    mandatory_refresh = Column(Boolean, nullable=False, default=False)

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
        return self.events.filter(CourseEvent.start > utcnow())
