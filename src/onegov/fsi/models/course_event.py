from uuid import uuid4

from sqlalchemy import Column, Boolean, Interval, ForeignKey, DateTime, \
    SmallInteger, Enum, Text
from sqlalchemy.orm import relationship, backref

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.reservation import reservation_table

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

    # Creator of this course event
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)

    status = Column(
        Enum(
            *COURSE_EVENT_STATUSES, name='status'
        ),
        nullable=False, default='created')

    attendees = relationship(
        CourseAttendee,
        secondary=reservation_table,
        primaryjoin=id == reservation_table.c.course_event_id,
        secondaryjoin=reservation_table.c.attendee_id == CourseAttendee.id,
        lazy='dynamic'
    )

    reservations = relationship(
        'Reservation',
        backref=backref(
            'course_event',
        ),
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    # hides from member roles
    hidden_from_public = Column(Boolean, nullable=False, default=False)

    @property
    def duration(self):
        return self.end - self.start

    @property
    def hidden(self):
        # Add criteria when a course should be hidden based on status or attr
        return self.hidden_from_public
