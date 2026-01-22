from __future__ import annotations

import datetime
import pytz

from collections import OrderedDict
from functools import cached_property
from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from sedate import utcnow, to_timezone
from sqlalchemy import (
    Column, Boolean, SmallInteger, Enum, Text, Interval, ForeignKey, desc, or_,
    and_)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session
from uuid import uuid4

from onegov.core.mail import Attachment
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.fsi import _
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_subscription import CourseSubscription
from onegov.fsi.models.course_subscription import subscription_table
from onegov.search import ORMSearchable


from typing import overload, Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable, Iterator
    from markupsafe import Markup
    from onegov.core.types import AppenderQuery
    from onegov.fsi.request import FsiRequest
    from sqlalchemy.orm import Query
    from typing import Self, TypeAlias
    from wtforms.fields.choices import _Choice
    from .course import Course
    from .course_notification_template import (
        CancellationTemplate, CourseNotificationTemplate, InfoTemplate,
        ReminderTemplate, SubscriptionTemplate
    )

    EventStatusType: TypeAlias = Literal[
        'created', 'confirmed', 'canceled', 'planned'
    ]


COURSE_EVENT_STATUSES: tuple[EventStatusType, ...] = (
    'created', 'confirmed', 'canceled', 'planned')
COURSE_EVENT_STATUSES_TRANSLATIONS = (
    _('Created'), _('Confirmed'), _('Canceled'), _('Planned'))


@overload
def course_status_choices(
    request: FsiRequest | None = None,
    as_dict: Literal[False] = False
) -> list[_Choice]: ...


@overload
def course_status_choices(
    request: FsiRequest | None,
    as_dict: Literal[True]
) -> list[dict[str, str]]: ...


@overload
def course_status_choices(
    request: FsiRequest | None = None,
    *,
    as_dict: Literal[True]
) -> list[dict[str, str]]: ...


def course_status_choices(
    request: FsiRequest | None = None,
    as_dict: bool = False
) -> list[_Choice] | list[dict[str, str]]:

    if request:
        translations: Iterable[str] = (
            request.translate(v) for v in COURSE_EVENT_STATUSES_TRANSLATIONS)
    else:
        translations = COURSE_EVENT_STATUSES_TRANSLATIONS

    zipped: zip[tuple[str, str]] = zip(COURSE_EVENT_STATUSES, translations)
    if as_dict:
        return [{val: key} for val, key in zipped]
    return list(zipped)  # type:ignore[return-value]


class CourseEvent(Base, TimestampMixin, ORMSearchable):

    default_reminder_before = datetime.timedelta(days=14)

    __tablename__ = 'fsi_course_events'

    fts_type_title = _('Course Events')
    fts_title_property = 'name'
    fts_properties = {
        'name': {'type': 'localized', 'weight': 'A'},
        'description': {'type': 'localized', 'weight': 'B'},
        'location': {'type': 'localized', 'weight': 'C'},
        'presenter_name': {'type': 'text', 'weight': 'A'},
        'presenter_company': {'type': 'text', 'weight': 'B'},
        'presenter_email': {'type': 'text', 'weight': 'A'},
    }

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    course_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('fsi_courses.id'),
        nullable=False
    )
    course: relationship[Course] = relationship(
        'Course',
        back_populates='events',
        lazy='joined'
    )

    @property
    def fts_public(self) -> bool:
        return not self.hidden_from_public

    @property
    def title(self) -> str:
        return str(self)

    @property
    def name(self) -> str:
        return self.course.name

    @property
    def lead(self) -> str:
        return (
            f'{self.location} - '
            f'{self.presenter_name} - '
            f'{self.presenter_company}'
        )

    @property
    def description(self) -> Markup:
        return self.course.description

    def __str__(self) -> str:
        start = to_timezone(
            self.start, 'Europe/Zurich').strftime('%d.%m.%Y %H:%M')
        return f'{self.name} - {start}'

    @cached_property
    def localized_start(self) -> datetime.datetime:
        return to_timezone(self.start, 'Europe/Zurich')

    @cached_property
    def localized_end(self) -> datetime.datetime:
        return to_timezone(self.end, 'Europe/Zurich')

    # Event specific information
    location: Column[str] = Column(Text, nullable=False)
    start: Column[datetime.datetime] = Column(UTCDateTime, nullable=False)
    end: Column[datetime.datetime] = Column(UTCDateTime, nullable=False)
    presenter_name: Column[str] = Column(Text, nullable=False)
    presenter_company: Column[str] = Column(Text, nullable=False)
    presenter_email: Column[str | None] = Column(Text)
    min_attendees: Column[int] = Column(
        SmallInteger,
        nullable=False,
        default=1
    )
    max_attendees: Column[int | None] = Column(SmallInteger, nullable=True)

    status: Column[EventStatusType] = Column(
        Enum(  # type:ignore[arg-type]
            *COURSE_EVENT_STATUSES, name='status'
        ),
        nullable=False, default='created')

    attendees: relationship[AppenderQuery[CourseAttendee]] = relationship(
        CourseAttendee,
        secondary=subscription_table,
        primaryjoin=id == subscription_table.c.course_event_id,
        secondaryjoin=subscription_table.c.attendee_id == CourseAttendee.id,
        lazy='dynamic',
        overlaps='course_event,attendee,subscriptions'  # type: ignore[call-arg]
    )

    subscriptions: relationship[AppenderQuery[CourseSubscription]]
    subscriptions = relationship(
        'CourseSubscription',
        back_populates='course_event',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    notification_templates: relationship[list[CourseNotificationTemplate]]
    notification_templates = relationship(
        'CourseNotificationTemplate',
        back_populates='course_event',
        cascade='all, delete-orphan',
    )

    # The associated notification templates
    # FIXME: Are some of these optional?
    info_template: relationship[InfoTemplate] = relationship(
        'InfoTemplate',
        uselist=False,
        overlaps='notification_templates'  # type: ignore[call-arg]
    )
    reservation_template: relationship[SubscriptionTemplate] = relationship(
        'SubscriptionTemplate',
        uselist=False,
        overlaps='notification_templates'  # type: ignore[call-arg]
    )
    cancellation_template: relationship[CancellationTemplate] = relationship(
        'CancellationTemplate',
        uselist=False,
        overlaps='notification_templates'  # type: ignore[call-arg]
    )
    reminder_template: relationship[ReminderTemplate] = relationship(
        'ReminderTemplate',
        uselist=False,
        overlaps='notification_templates'  # type: ignore[call-arg]
    )

    # hides for members/editors
    hidden_from_public: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # to a locked event, only an admin can place subscriptions
    # FIXME: Is this intentionally nullable?
    locked_for_subscriptions: Column[bool | None] = Column(
        Boolean,
        default=False
    )

    # when before course start schedule reminder email
    schedule_reminder_before: Column[datetime.timedelta] = Column(
        Interval,
        nullable=False,
        default=default_reminder_before)

    @property
    def description_html(self) -> Markup:
        """
        Returns the portrait that is saved as HTML from the redactor js
        plugin.
        """
        return self.description

    @hybrid_property
    def scheduled_reminder(self) -> datetime.datetime:
        return self.start + self.schedule_reminder_before

    @hybrid_property
    def next_event_start(self) -> datetime.datetime:
        # XXX this is currently wrong, since the refresh_interval was moved
        # to the course. Before that the it looked like this, which now fails:
        # return self.end + refresh_interval
        return self.end

    @property
    def duration(self) -> datetime.timedelta:
        return self.end - self.start

    @property
    def hidden(self) -> bool:
        # Add criteria when a course should be hidden based on status or attr
        return self.hidden_from_public or self.course.hidden_from_public

    @cached_property
    def cached_reservation_count(self) -> int:
        return self.subscriptions.count()

    @property
    def available_seats(self) -> int | None:
        if self.max_attendees:
            seats = self.max_attendees - self.cached_reservation_count
            return max(seats, 0)
        return None

    @property
    def booked(self) -> bool:
        if not self.max_attendees:
            return False
        return self.max_attendees <= self.cached_reservation_count

    @property
    def bookable(self) -> bool:
        return not self.booked and self.start > utcnow()

    @property
    def is_past(self) -> bool:
        return self.start < utcnow()

    @property
    def locked(self) -> bool:
        # Basically locked for non-admins
        return self.locked_for_subscriptions or not self.bookable

    # FIXME: Use TypedDict
    @property
    def duplicate_dict(self) -> dict[str, Any]:
        return OrderedDict(
            location=self.location,
            course_id=self.course_id,
            presenter_name=self.presenter_name,
            presenter_company=self.presenter_company,
            presenter_email=self.presenter_email,
            min_attendees=self.min_attendees,
            max_attendees=self.max_attendees,
            status='created',
            hidden_from_public=self.hidden_from_public
        )

    @property
    def duplicate(self) -> Self:
        return self.__class__(**self.duplicate_dict)

    def has_reservation(self, attendee_id: uuid.UUID) -> bool:
        return self.subscriptions.filter_by(
            attendee_id=attendee_id).first() is not None

    @overload
    def excluded_subscribers(
        self,
        year: int | None = None,
        as_uids: Literal[True] = True,
        exclude_inactive: bool = True
    ) -> Query[tuple[uuid.UUID]]: ...

    @overload
    def excluded_subscribers(
        self,
        year: int | None,
        as_uids: Literal[False],
        exclude_inactive: bool = True
    ) -> Query[CourseAttendee]: ...

    @overload
    def excluded_subscribers(
        self,
        year: int | None = None,
        *,
        as_uids: Literal[False],
        exclude_inactive: bool = True
    ) -> Query[CourseAttendee]: ...

    @overload
    def excluded_subscribers(
        self,
        year: int | None,
        as_uids: bool,
        exclude_inactive: bool = True
    ) -> Query[tuple[uuid.UUID]] | Query[CourseAttendee]: ...

    def excluded_subscribers(
        self,
        year: int | None = None,
        as_uids: bool = True,
        exclude_inactive: bool = True
    ) -> Query[tuple[uuid.UUID]] | Query[CourseAttendee]:
        """
        Returns a list of attendees / names tuple of UIDS
        of attendees that have booked one of the events of a course in
        the given year."""
        session = object_session(self)

        excl = session.query(CourseAttendee.id if as_uids else CourseAttendee)
        excl = excl.join(CourseSubscription).join(CourseEvent)

        year = year or datetime.datetime.today().year
        bounds = (
            datetime.datetime(year, 1, 1, tzinfo=pytz.utc),
            datetime.datetime(year, 12, 31, tzinfo=pytz.utc)
        )

        general_exclusions = [
            CourseSubscription.course_event_id == self.id
        ]

        if exclude_inactive:
            general_exclusions.append(CourseAttendee.active == False)

        return excl.filter(
            or_(
                and_(
                    CourseEvent.course_id == self.course.id,
                    CourseEvent.start >= bounds[0],
                    CourseEvent.end <= bounds[1],
                ),
                *general_exclusions
            )
        )

    @overload
    def possible_subscribers(
        self,
        external_only: bool = False,
        year: int | None = None,
        as_uids: Literal[False] = False,
        exclude_inactive: bool = True,
        auth_attendee: CourseAttendee | None = None
    ) -> Query[CourseAttendee]: ...

    @overload
    def possible_subscribers(
        self,
        external_only: bool,
        year: int | None,
        as_uids: Literal[True],
        exclude_inactive: bool = True,
        auth_attendee: CourseAttendee | None = None
    ) -> Query[tuple[uuid.UUID]]: ...

    @overload
    def possible_subscribers(
        self,
        external_only: bool = False,
        year: int | None = None,
        *,
        as_uids: Literal[True],
        exclude_inactive: bool = True,
        auth_attendee: CourseAttendee | None = None
    ) -> Query[tuple[uuid.UUID]]: ...

    def possible_subscribers(
        self,
        external_only: bool = False,
        year: int | None = None,
        as_uids: bool = False,
        exclude_inactive: bool = True,
        auth_attendee: CourseAttendee | None = None
    ) -> Query[tuple[uuid.UUID]] | Query[CourseAttendee]:
        """Returns the list of possible bookers. Attendees that already have
        a subscription for the parent course in the same year are excluded."""
        session = object_session(self)

        excluded = (
            self.excluded_subscribers(year, exclude_inactive)
            .scalar_subquery()  # type: ignore[union-attr]
        )

        # Use this because its less costly
        query = session.query(as_uids and CourseAttendee.id or CourseAttendee)

        if external_only:
            query = query.filter(CourseAttendee.user_id == None)

        if auth_attendee and auth_attendee.role == 'editor':
            attendee_permissions = auth_attendee.permissions or []
            query = query.filter(
                or_(
                    CourseAttendee.organisation.in_(attendee_permissions),
                    CourseAttendee.id == auth_attendee.id
                )
            )

        query = query.filter(CourseAttendee.id.notin_(excluded))

        if not as_uids:
            query = query.order_by(
                CourseAttendee.last_name, CourseAttendee.first_name)
        return query

    @property
    def email_recipients(self) -> Iterator[str]:
        return (att.email for att in self.attendees)

    def as_ical(self, event_url: str | None = None) -> bytes:
        modified = self.modified or self.created or utcnow()

        vevent = vEvent()
        vevent.add('uid', f'{self.name}-{self.start}-{self.end}@onegov.fsi')
        vevent.add('summary', self.name)
        vevent.add('dtstart', self.start)
        vevent.add('dtend', self.end)
        vevent.add('last-modified', modified)
        vevent.add('dtstamp', modified)
        vevent.add('location', self.location)
        vevent.add('description', self.description)
        vevent.add('tags', ['FSI'])
        if event_url:
            vevent.add('url', event_url)

        vcalendar = vCalendar()
        vcalendar.add('prodid', '-//OneGov//onegov.fsi//')
        vcalendar.add('version', '2.0')
        vcalendar.add_component(vevent)

        return vcalendar.to_ical()

    def as_ical_attachment(self, url: str | None = None) -> Attachment:
        return Attachment(
            filename=self.name.lower().replace(' ', '_') + '.ics',
            content=self.as_ical(url),
            content_type='text/calendar'
        )

    def can_book(
        self,
        attendee_or_id: CourseAttendee | uuid.UUID | str,
        year: int | None = None
    ) -> bool:

        att_id = attendee_or_id
        if isinstance(attendee_or_id, CourseAttendee):
            att_id = attendee_or_id.id
        for entry_id, in self.excluded_subscribers(year, as_uids=True):
            if str(entry_id) == str(att_id):
                return False
        return True

    def exceeds_six_year_limit(self, attendee_id: str | UUID,
                               request: FsiRequest) -> bool:
        last_subscribed_event = request.session.query(
            CourseEvent).join(CourseSubscription).filter(
            CourseSubscription.attendee_id == attendee_id
            ).order_by(desc(CourseEvent.start)).first()

        if last_subscribed_event is None:
            return True
        elif (
            # Chosen event needs to start at least 6 years after the last
            # subscribed event
            self.start < datetime.datetime(
                last_subscribed_event.start.year + 6, 1, 1, tzinfo=pytz.utc)
        ):
            return False
        return True
