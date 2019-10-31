from uuid import uuid4
from sqlalchemy import Column, Text, ForeignKey, JSON, Enum
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.core.orm.mixins import meta_property
from sqlalchemy.orm import relationship, object_session, backref

from onegov.user import User

ATTENDEE_TITLES = ('mr', 'ms', 'none')


class CourseAttendee(Base):
    """
    Comprises the user base mirrored by one-to-one relationship with
    onegov.user.User which is linked to the LDAP System including
    external users, that are created by an admin role.

    The onegov.user.User model should only contain email and role
    and is only used for authentication and permissions.

    All other attributes should be stored in here.

    Entries
    - external attendees: the do not have a link to a user
    - CourseAttendees linked to an admin role, aka Kursverantwortlicher
    - CourseAttendess linked to a member role, aka Kursbesucher

    """

    __tablename__ = 'fsi_attendees'

    # is null if its an external attendee
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    user = relationship("User", backref=backref("attendee", uselist=False))
    title = Column(
        Enum(*ATTENDEE_TITLES, name='title'), nullable=False, default='none')

    id = Column(UUID, primary_key=True, default=uuid4)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    _email = Column(Text, unique=True)
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
    def role(self):
        if not self.user_id:
            return 'member'
        return self.user.role

    @property
    def email(self):
        """Needs a switch for external users"""
        if not self.user_id:
            return self._email
        return self.user.username

    @email.setter
    def email(self, value):
        self._email = value

    @property
    def course_events(self):
        """
        Will return the query to for not completed (future) courses events
         the attendee has a reservation record.
        """
        from onegov.fsi.models.course_event import CourseEvent  # circular
        from onegov.fsi.models.reservation import Reservation  # circular

        session = object_session(self)
        result = session.query(CourseEvent).join(Reservation)
        result = result.filter(Reservation.attendee_id == self.id)
        result = result.filter(Reservation.event_completed == False)
        return result

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
        result = result.filter(Reservation.event_completed == True)
        result = result.filter(Course.mandatory_refresh == True)
        return result
