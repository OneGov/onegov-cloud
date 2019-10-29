from uuid import uuid4

from sqlalchemy import Column, Boolean, Interval, ForeignKey, DateTime, \
    SmallInteger, Enum, Text

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID

COURSE_EVENT_STATUSES = ('created', 'confirmed', 'canceled', 'planned')


class CourseEvent(Base, TimestampMixin):

    __tablename__ = 'fsi_course_events'

    id = Column(UUID, primary_key=True, default=uuid4)
    course_id = Column(UUID, ForeignKey('fsi_courses.id'), nullable=False)

    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    # Short description
    name = Column(Text, nullable=False)

    presenter_name = Column(Text, nullable=False)
    presenter_company = Column(Text, nullable=False)

    min_attendees = Column(SmallInteger, nullable=False, default=1)
    max_attendees = Column(SmallInteger, nullable=True)

    # If the course has to be refreshed after some interval
    mandatory_refresh = Column(Boolean, nullable=False, default=False)

    # Refresh interval
    refresh_interval = Column(Interval)

    # Creator of this course event
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)

    status = Column(
        Enum(
            *COURSE_EVENT_STATUSES, name='status'
        ),
        nullable=False, default='created')

    @property
    def duration(self):
        return self.end - self.start