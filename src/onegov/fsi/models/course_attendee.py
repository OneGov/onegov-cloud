from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.orm import Base
from onegov.core.orm.types import UUID, JSON
from sqlalchemy import Boolean, Index
from sqlalchemy import Computed  # type:ignore[attr-defined]
from onegov.search import ORMSearchable, Searchable
from sedate import utcnow
from sqlalchemy import Column, Text, ForeignKey, ARRAY, desc
from sqlalchemy.orm import relationship, object_session, backref
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user import User
    from .course_subscription import CourseSubscription


external_attendee_org = "Externe Kursteilnehmer"


class CourseAttendee(Base, ORMSearchable):
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

    es_properties = {
        'first_name': {'type': 'text'},
        'last_name': {'type': 'text'},
        'organisation': {'type': 'text'},
        'email': {'type': 'text'},
        'title': {'type': 'text'},
    }

    es_public = False

    id = Column(UUID, primary_key=True, default=uuid4)

    # is null if its an external attendee
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    user: 'relationship[User | None]' = relationship(
        "User", backref=backref("attendee", uselist=False))

    # mirrors user active property
    active = Column(Boolean, nullable=False, default=True)

    # mirrors the source_id field from user due to performance reasons
    source_id = Column(Text, nullable=True)

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

    subscriptions: 'relationship[list[CourseSubscription]]' = relationship(
        'CourseSubscription',
        backref='attendee',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    fts_idx = Column(TSVECTOR, Computed('', persisted=True))

    __table_args__ = (
        Index('fts_idx', fts_idx, postgresql_using='gin'),
    )

    @staticmethod
    def psql_tsvector_string():
        """
        index is built on the following columns
        """
        return Searchable.create_tsvector_string('first_name', 'last_name',
                                                 'organisation', '_email')

    @property
    def title(self):
        return ' '.join((
            p for p in (
                self.first_name,
                self.last_name,
            ) if p
        )) or self.email

    @property
    def lead(self):
        return self.organisation

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
         the attendee has a subscription record.
        """
        from onegov.fsi.models import CourseEvent  # circular
        from onegov.fsi.models import CourseSubscription  # circular

        session = object_session(self)
        result = session.query(CourseEvent).join(CourseSubscription)
        result = result.filter(CourseSubscription.attendee_id == self.id)
        result = result.filter(CourseSubscription.event_completed == False)
        result = result.filter(CourseEvent.start > utcnow())

        return result

    @property
    def confirmed_course_events(self):
        """ Registered future course events which have been confirmed """
        from onegov.fsi.models import CourseEvent
        return self.course_events.filter(CourseEvent.status == 'confirmed')

    @property
    def total_done_course_events(self):
        from onegov.fsi.models import CourseSubscription  # circular
        return self.subscriptions.filter(
            CourseSubscription.event_completed == True)

    @property
    def repeating_courses(self):
        """
        Will return query to filter for all upcoming courses the attendee
        has to refresh.

        This is necessary to answer:
            if one course, how many course events has an attendee:
                a) not registered if he had to
            Or from the perspective of a course_event, was there a succeeding
            course event in the range of the refresh interval?

        """

        # circular imports
        from onegov.fsi.models import Course
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseSubscription

        session = object_session(self)

        result = session.query(CourseEvent).join(Course)\
            .filter(Course.mandatory_refresh == True)

        result = result.join(CourseSubscription)
        result = result.filter(CourseSubscription.attendee_id == self.id)
        result = result.filter(CourseSubscription.event_completed == True)
        result = result.filter(CourseEvent.next_event_start > utcnow())
        return result

    @property
    def undone_registered_courses(self):
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseSubscription

        session = object_session(self)
        result = session.query(CourseEvent).join(CourseSubscription)
        result = result.filter(CourseEvent.status == 'confirmed')
        result = result.filter(CourseEvent.start < utcnow())
        result = result.filter(CourseSubscription.attendee_id == self.id)
        result = result.filter(CourseSubscription.event_completed == False)
        return result

    def possible_course_events(self, show_hidden=True, show_locked=False):
        """Used for the subscription form. Should exclude past courses
        and courses already registered"""
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseSubscription

        session = object_session(self)
        excl = session.query(CourseEvent.id).join(CourseSubscription)
        excl = excl.filter(CourseSubscription.attendee_id == self.id)
        excl = excl.subquery('excl')
        result = session.query(CourseEvent).filter(CourseEvent.id.notin_(excl))
        result = result.filter(CourseEvent.start > utcnow())
        if not show_hidden:
            result = result.filter(CourseEvent.hidden_from_public == False)
        if not show_locked:
            result = result.filter(
                CourseEvent.locked_for_subscriptions == False)

        result = result.order_by(desc(CourseEvent.start))
        return result
