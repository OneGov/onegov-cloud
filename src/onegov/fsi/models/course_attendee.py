from uuid import uuid4
from sqlalchemy import Column, Text, ForeignKey, JSON, Enum
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.core.orm.mixins import meta_property
from sqlalchemy.orm import relationship, object_session

ATTENDEE_TITLES = ('mr', 'ms', 'none')


class CourseAttendee(Base):

    __tablename__ = 'fsi_attendees'

    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    title = Column(
        Enum(*ATTENDEE_TITLES, name='title'), nullable=False, default='none')

    id = Column(UUID, primary_key=True, default=uuid4)
    first_name = Column(Text)
    last_name = Column(Text)
    email = Column(Text)
    address = meta_property('address')

    # Description of attendee is a placeholder
    dummy_desc = Column(Text)

    def __str__(self):
        return f'{self.last_name or "", self.first_name or self.dummy_desc}'

    meta = Column(JSON, nullable=True, default=dict)

    reservations = relationship(
        'Reservation',
        backref='attendee',
        lazy='dynamic',
        cascade='all, delete-orphan')

    @property
    def course_events(self):
        raise NotImplementedError

    def upcoming_courses(self):
        """
        Will return the query to filter for all courses the attendee
        has done with mandatory_refresh.
        It delivers wrong results if a reservation for a future event
        is marked as passed, though for the sake of speed.
        """
        from onegov.fsi.models.course_event import CourseEvent      # circular
        from onegov.fsi.models.course import Course                 # circular
        from onegov.fsi.models.reservation import Reservation       # circular

        session = object_session(self)
        result = session.query(Course).join(CourseEvent, Reservation)
        result = result.filter(Reservation.attendee_id == self.id)
        result = result.filter(Reservation.event_completed==True)
        result = result.filter(Course.mandatory_refresh==True)
        return result

    @classmethod
    def as_placeholder(cls, dummy_desc, **kwargs):
        return cls(dummy_desc=dummy_desc, **kwargs)

