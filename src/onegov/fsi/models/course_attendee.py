from uuid import uuid4
from sqlalchemy import Column, Text, ForeignKey, JSON, Enum
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.core.orm.mixins import meta_property
from sqlalchemy.orm import relationship, object_session, backref

from onegov.user import User

ATTENDEE_TITLES = ('mr', 'ms', 'none')


class CourseAttendee(Base):

    __tablename__ = 'fsi_attendees'

    # is null if its an external attendee
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    user = relationship("User", backref=backref("attendee", uselist=False))
    title = Column(
        Enum(*ATTENDEE_TITLES, name='title'), nullable=False, default='none')

    id = Column(UUID, primary_key=True, default=uuid4)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    address = meta_property('address')

    def __str__(self):
        return f'{self.last_name}, {self.first_name}'

    meta = Column(JSON, nullable=True, default=dict)

    reservations = relationship(
        'Reservation',
        backref='attendee',
        lazy='dynamic',
        cascade='all, delete-orphan')

    templates = relationship(
        'FsiNotificationTemplate',
        backref='owner',
    )

    @property
    def auth_user(self):
        """Get the onegov.user.User behind the attendee"""
        if not self.user_id:
            return None
        return object_session(self).query(User).filter_by(
            id=self.user_id).one()

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
        result = result.filter(Reservation.attendee_email == self.email)
        result = result.filter(Reservation.event_completed == True)
        result = result.filter(Course.mandatory_refresh == True)
        return result
