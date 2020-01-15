from uuid import uuid4

from sedate import utcnow
from sqlalchemy import Column, Text, ForeignKey, ARRAY

from onegov.core.orm import Base
from onegov.core.orm.types import UUID, JSON
from sqlalchemy.orm import relationship, object_session, backref


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

    id = Column(UUID, primary_key=True, default=uuid4)

    # is null if its an external attendee
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    user = relationship("User", backref=backref("attendee", uselist=False))

    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)

    # The organization this user belongs to, which may be a path like this:
    #
    # BD / HBA / Planungsbaukommission
    #
    # This is equal to Baudirektion / Hochbauamt / Planungsbaukommission.
    # The path may also be shorter:
    #
    # BD / HBA
    #
    # Or be missing all together.
    #
    # This is used for permissions. Editors are limited to access the users
    # for whose organization they have access by full path / exact match.
    #
    # So a user would have to have get permission for both
    # BD / HBA / Planungsbaukommission" and "BD / HBA" to access all of
    # "BD / HBA / *"
    #
    organisation = Column(Text, nullable=True)

    permissions = Column(ARRAY(Text), default=list)

    _email = Column(Text, unique=True)

    def __str__(self):
        if self.first_name and self.last_name:
            text = f'{self.last_name}, {self.first_name}'
            # if self.user and (self.user.source and self.user.source_id):
            #     text += f' - {self.user.source_id}'
            return text
        mail = self.email
        if mail:
            return mail
        return 'NO NAME NO EMAIL'

    meta = Column(JSON, nullable=True, default=dict)

    reservations = relationship(
        'CourseReservation',
        backref='attendee',
        lazy='dynamic',
        cascade='all, delete-orphan')

    @property
    def is_external(self):
        return self.user_id is None

    @property
    def role(self):
        if not self.user_id:
            # External attendees
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
        Will return the query for not completed (future) courses events
         the attendee has a reservation record.
        """
        from onegov.fsi.models import CourseEvent  # circular
        from onegov.fsi.models import CourseReservation  # circular

        session = object_session(self)
        result = session.query(CourseEvent).join(CourseReservation)
        result = result.filter(CourseReservation.attendee_id == self.id)
        result = result.filter(CourseReservation.event_completed == False)
        result = result.filter(CourseEvent.start > utcnow())

        return result

    @property
    def confirmed_course_events(self):
        """ Registered future course events which have been confirmed """
        from onegov.fsi.models import CourseEvent
        return self.course_events.filter(CourseEvent.status == 'confirmed')

    @property
    def total_done_course_events(self):
        from onegov.fsi.models import CourseReservation  # circular
        return self.reservations.filter(
            CourseReservation.event_completed == True)

    @property
    def repeating_courses(self):
        """
        Will return query to filter for all upcoming courses the attendee
        has to refresh.

        TODO: First implement a foreign key to itself or fk to model course

        This is necessary to answer:
            if one course, how many course events has an attendee:
                a) not registered if he had to
            Or from the perspective of a course_event, was there a succeeding
            course event in the range of the refresh interval?

        """

        # circular imports
        from onegov.fsi.models import Course
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseReservation

        session = object_session(self)

        result = session.query(CourseEvent).join(Course)\
            .filter(Course.mandatory_refresh == True)

        result = result.join(CourseReservation)
        result = result.filter(CourseReservation.attendee_id == self.id)
        result = result.filter(CourseReservation.event_completed == True)
        result = result.filter(CourseEvent.next_event_start > utcnow())
        return result

    @property
    def undone_registered_courses(self):
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseReservation

        session = object_session(self)
        result = session.query(CourseEvent).join(CourseReservation)
        result = result.filter(CourseEvent.status == 'confirmed')
        result = result.filter(CourseEvent.start < utcnow())
        result = result.filter(CourseReservation.attendee_id == self.id)
        result = result.filter(CourseReservation.event_completed == False)
        return result

    def possible_course_events(self, show_hidden=True):
        """Used for the reservation form. Should exlucde past courses
        and courses already registered"""
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseReservation

        session = object_session(self)
        excl = session.query(CourseEvent.id).join(CourseReservation)
        excl = excl.filter(CourseReservation.attendee_id == self.id)
        excl = excl.subquery('excl')
        result = session.query(CourseEvent).filter(CourseEvent.id.notin_(excl))
        result = result.filter(CourseEvent.start > utcnow())
        if not show_hidden:
            result = result.filter(CourseEvent.hidden_from_public == False)
        return result
