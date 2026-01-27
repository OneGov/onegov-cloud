from __future__ import annotations

import datetime
import pytz
from onegov.core.orm import Base
from onegov.core.orm.types import UUID, JSON
from onegov.fsi.i18n import _
from onegov.search import ORMSearchable
from sedate import utcnow
from sqlalchemy import Boolean, Column, Text, ForeignKey, ARRAY, desc
from sqlalchemy.orm import relationship, object_session, backref
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.core.types import AppenderQuery
    from onegov.user import User
    from sqlalchemy.orm import Query
    from .course_event import CourseEvent
    from .course_subscription import CourseSubscription


external_attendee_org = 'Externe Kursteilnehmer'


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

    fts_type_title = _('Attendees')
    fts_public = False
    fts_title_property = 'title'
    fts_properties = {
        # NOTE: We use both individual properties and title, it's
        #       probably better to only use the title
        'first_name': {'type': 'text', 'weight': 'A'},
        'last_name': {'type': 'text', 'weight': 'A'},
        'email': {'type': 'text', 'weight': 'A'},
        'title': {'type': 'text', 'weight': 'A'},
        'organisation': {'type': 'text', 'weight': 'B'},
    }

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    # is null if its an external attendee
    user_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('users.id'),
        nullable=True
    )
    # FIXME: It's not great that we insert a backref on User across
    #        module boundaries here. This technically violates the
    #        separation of modules. Do we need this?
    user: relationship[User | None] = relationship(
        'User', backref=backref('attendee', uselist=False))

    # mirrors user active property
    active: Column[bool] = Column(Boolean, nullable=False, default=True)

    # mirrors the source_id field from user due to performance reasons
    source_id: Column[str | None] = Column(Text, nullable=True)

    first_name: Column[str | None] = Column(Text, nullable=True)
    last_name: Column[str | None] = Column(Text, nullable=True)

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
    organisation: Column[str | None] = Column(Text, nullable=True)

    permissions: Column[list[str] | None] = Column(ARRAY(Text), default=list)

    _email: Column[str | None] = Column(Text, unique=True)

    def __str__(self) -> str:
        if self.first_name and self.last_name:
            text = f'{self.last_name}, {self.first_name}'
            # if self.user and (self.user.source and self.user.source_id):
            #     text += f' - {self.user.source_id}'
            return text
        mail = self.email
        if mail:
            return mail
        return 'NO NAME NO EMAIL'

    meta: Column[dict[str, Any] | None] = Column(
        JSON,
        # FIXME: Why is this nullable=True if we set a default?
        nullable=True,
        default=dict
    )

    subscriptions: relationship[AppenderQuery[CourseSubscription]] = (
        relationship(
            'CourseSubscription',
            back_populates='attendee',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
    )

    @property
    def title(self) -> str:
        return ' '.join(
            part
            for part in (self.first_name, self.last_name)
            if part
        ) or self.email

    @property
    def lead(self) -> str | None:
        return self.organisation

    @property
    def is_external(self) -> bool:
        return self.user_id is None

    @property
    def role(self) -> str:
        if not self.user_id:
            # External attendees
            return 'member'
        assert self.user is not None
        return self.user.role

    @property
    def email(self) -> str:
        """Needs a switch for external users"""
        if not self.user_id:
            # FIXME: In the tests there's a scenario where this is
            #        allowed to be None, but there are a ton of places
            #        where it isn't allowed to be None, so we should
            #        probably disallow it and properly deal with it
            #        in places where it's allowed to be None
            return self._email  # type:ignore[return-value]
        assert self.user is not None
        return self.user.username

    @email.setter
    def email(self, value: str) -> None:
        self._email = value

    @property
    def course_events(self) -> Query[CourseEvent]:
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
    def confirmed_course_events(self) -> Query[CourseEvent]:
        """ Registered future course events which have been confirmed """
        from onegov.fsi.models import CourseEvent
        return self.course_events.filter(CourseEvent.status == 'confirmed')

    @property
    def total_done_course_events(self) -> Query[CourseSubscription]:
        from onegov.fsi.models import CourseSubscription  # circular
        return self.subscriptions.filter(
            CourseSubscription.event_completed == True)

    @property
    def repeating_courses(self) -> Query[CourseEvent]:
        """
        Will return query to filter for all upcoming courses the attendee
        has to refresh.

        This is necessary to answer: if one course, how many course events
        has an attendee: a) not registered if he had to or b) from the
        perspective of a course_event, was there a succeeding course event in
        the range of the refresh interval?

        """

        # circular imports
        from onegov.fsi.models import Course
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseSubscription

        session = object_session(self)

        return (
            session.query(CourseEvent)
            .join(Course)
            .filter(Course.mandatory_refresh == True)
            .join(CourseSubscription)
            .filter(CourseSubscription.attendee_id == self.id)
            .filter(CourseSubscription.event_completed == True)
            .filter(CourseEvent.next_event_start > utcnow())
        )

    @property
    def undone_registered_courses(self) -> Query[CourseEvent]:
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseSubscription

        session = object_session(self)
        result = session.query(CourseEvent).join(CourseSubscription)
        result = result.filter(CourseEvent.status == 'confirmed')
        result = result.filter(CourseEvent.start < utcnow())
        result = result.filter(CourseSubscription.attendee_id == self.id)
        result = result.filter(CourseSubscription.event_completed == False)
        return result

    def possible_course_events(
        self,
        show_hidden: bool = True,
        show_locked: bool = False
    ) -> Query[CourseEvent]:
        """Used for the subscription form. Should exclude past courses
        and courses already registered"""
        from onegov.fsi.models import CourseEvent
        from onegov.fsi.models import CourseSubscription

        session = object_session(self)
        excl = session.query(CourseEvent.id).join(CourseSubscription)
        excl = excl.filter(CourseSubscription.attendee_id == self.id)
        excl = excl.subquery('excl')

        last_subscribed_event = session.query(
            CourseEvent).join(CourseSubscription).filter(
            CourseSubscription.attendee_id == self.id).order_by(
            desc(CourseEvent.start)).first()

        result = session.query(CourseEvent).filter(CourseEvent.id.notin_(excl))
        result = result.filter(CourseEvent.start > utcnow())
        if last_subscribed_event:
            # Suggested events need to start at least 6 years after the last
            # subscribed event
            result = result.filter(
                CourseEvent.start > datetime.datetime(
                    last_subscribed_event.start.year + 6, 1, 1,
                    tzinfo=pytz.utc))

        if not show_hidden:
            result = result.filter(CourseEvent.hidden_from_public == False)
        if not show_locked:
            result = result.filter(
                CourseEvent.locked_for_subscriptions == False)

        result = result.order_by(desc(CourseEvent.start))
        return result
