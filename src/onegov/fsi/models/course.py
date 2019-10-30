from uuid import uuid4

from sedate import utcnow
from sqlalchemy import Column, Boolean, Interval, ForeignKey, Text, and_
from sqlalchemy.orm import relationship, backref
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.fsi.models.course_event import CourseEvent


class Course(Base, TimestampMixin):

    __tablename__ = 'fsi_courses'

    id = Column(UUID, primary_key=True, default=uuid4)

    description = Column(Text, nullable=False)
    # Short description
    name = Column(Text, nullable=False)

    presenter_name = Column(Text, nullable=False)
    presenter_company = Column(Text, nullable=False)

    # If the course has to be refreshed after some interval
    mandatory_refresh = Column(Boolean, nullable=False)
    # Refresh interval
    refresh_interval = Column(Interval, nullable=False)

    # Creator of this course
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)

    # Each course can have n events
    events = relationship(
        CourseEvent,
        cascade='all, delete-orphan',
        lazy='dynamic',
        # backref=backref('course', lazy='joined')
    )

    upcoming_events = relationship(
        'CourseEvent',
        primaryjoin=and_(CourseEvent.course_id==id,
                    CourseEvent.start > utcnow()))

    hidden_from_public = Column(Boolean, nullable=False, default=False)

    @property
    def hidden(self):
        return self.hidden_from_public

    def next_event(self):
        return self.events.filter(
            CourseEvent.start > utcnow()).order_by(
            CourseEvent.start
        ).first()
