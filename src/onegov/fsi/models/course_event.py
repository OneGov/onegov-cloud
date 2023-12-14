import datetime
import pytz

from collections import OrderedDict
from functools import cached_property
from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from sedate import utcnow, to_timezone
from sqlalchemy import (
    Column, Boolean, SmallInteger, Enum, Text, Interval, ForeignKey, or_, and_)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref, object_session
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


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .course import Course
    from .course_notification_template import (
        CancellationTemplate, CourseNotificationTemplate, InfoTemplate,
        ReminderTemplate, SubscriptionTemplate
    )

COURSE_EVENT_STATUSES = ('created', 'confirmed', 'canceled', 'planned')
COURSE_EVENT_STATUSES_TRANSLATIONS = (
    _('Created'), _('Confirmed'), _('Canceled'), _('Planned'))


# for forms...
def course_status_choices(request=None, as_dict=False):

    if request:
        translations = (
            request.translate(v) for v in COURSE_EVENT_STATUSES_TRANSLATIONS)
    else:
        translations = COURSE_EVENT_STATUSES_TRANSLATIONS

    return tuple(
        as_dict and {val: key} or (val, key)
        for val, key in zip(COURSE_EVENT_STATUSES, translations)
    )


class CourseEvent(Base, TimestampMixin, ORMSearchable):

    default_reminder_before = datetime.timedelta(days=14)

    __tablename__ = 'fsi_course_events'

    es_properties = {
        'name': {'type': 'localized'},
        'description': {'type': 'localized'},
        'location': {'type': 'localized'},
        'presenter_name': {'type': 'text'},
        'presenter_company': {'type': 'text'},
        'presenter_email': {'type': 'text'},
    }

    id = Column(UUID, primary_key=True, default=uuid4)

    course_id = Column(UUID, ForeignKey('fsi_courses.id'), nullable=False)
    course: 'relationship[Course]' = relationship(
        'Course',
        backref=backref('events', lazy='dynamic'),
        lazy='joined'
    )

    @property
    def es_public(self):
        return not self.hidden_from_public

    @property
    def title(self):
        return str(self)

    @property
    def name(self):
        return self.course.name

    @property
    def lead(self):
        return (
            f'{self.location} - '
            f'{self.presenter_name} - '
            f'{self.presenter_company}'
        )

    @property
    def description(self):
        return self.course.description

    def __str__(self):
        start = to_timezone(
            self.start, 'Europe/Zurich').strftime('%d.%m.%Y %H:%M')
        return f"{self.name} - {start}"

    @cached_property
    def localized_start(self):
        return to_timezone(self.start, 'Europe/Zurich')

    @cached_property
    def localized_end(self):
        return to_timezone(self.end, 'Europe/Zurich')

    # Event specific information
    location = Column(Text, nullable=False)
    start = Column(UTCDateTime, nullable=False)
    end = Column(UTCDateTime, nullable=False)
    presenter_name = Column(Text, nullable=False)
    presenter_company = Column(Text, nullable=False)
    presenter_email = Column(Text)
    min_attendees = Column(SmallInteger, nullable=False, default=1)
    max_attendees = Column(SmallInteger, nullable=True)

    status = Column(
        Enum(
            *COURSE_EVENT_STATUSES, name='status'
        ),
        nullable=False, default='created')

    attendees: 'relationship[list[CourseAttendee]]' = relationship(
        CourseAttendee,
        secondary=subscription_table,
        primaryjoin=id == subscription_table.c.course_event_id,
        secondaryjoin=subscription_table.c.attendee_id == CourseAttendee.id,
        lazy='dynamic'
    )

    subscriptions: 'relationship[list[CourseSubscription]]' = relationship(
        'CourseSubscription',
        backref=backref(
            'course_event',
            lazy='joined'
        ),
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    notification_templates: 'relationship[list[CourseNotificationTemplate]]'
    notification_templates = relationship(
        'CourseNotificationTemplate',
        back_populates='course_event',
        cascade='all, delete-orphan',
    )

    # The associated notification templates
    # FIXME: Are some of these optional?
    info_template: 'relationship[InfoTemplate]' = relationship(
        "InfoTemplate", uselist=False)
    reservation_template: 'relationship[SubscriptionTemplate]' = relationship(
        "SubscriptionTemplate", uselist=False)
    cancellation_template: 'relationship[CancellationTemplate]' = relationship(
        "CancellationTemplate", uselist=False)
    reminder_template: 'relationship[ReminderTemplate]' = relationship(
        "ReminderTemplate", uselist=False)

    # hides for members/editors
    hidden_from_public = Column(Boolean, nullable=False, default=False)

    # to a locked event, only an admin can place subscriptions
    locked_for_subscriptions = Column(Boolean, default=False)

    # when before course start schedule reminder email
    schedule_reminder_before = Column(
        Interval,
        nullable=False,
        default=default_reminder_before)

    @property
    def description_html(self):
        """
        Returns the portrait that is saved as HTML from the redactor js
        plugin.
        """
        return self.description

    @hybrid_property
    def scheduled_reminder(self):
        return self.start + self.schedule_reminder_before

    @hybrid_property
    def next_event_start(self):
        # XXX this is currently wrong, since the refresh_interval was moved
        # to the course. Before that the it looked like this, which now fails:
        # return self.end + refresh_interval
        return self.end

    @property
    def duration(self):
        return self.end - self.start

    @property
    def hidden(self):
        # Add criteria when a course should be hidden based on status or attr
        return self.hidden_from_public or self.course.hidden_from_public

    @cached_property
    def cached_reservation_count(self):
        return self.subscriptions.count()

    @property
    def available_seats(self):
        if self.max_attendees:
            seats = self.max_attendees - self.cached_reservation_count
            return 0 if seats < 0 else seats
        return None

    @property
    def booked(self):
        if not self.max_attendees:
            return False
        return self.max_attendees <= self.cached_reservation_count

    @property
    def bookable(self):
        return not self.booked and self.start > utcnow()

    @property
    def is_past(self):
        return self.start < utcnow()

    @property
    def locked(self):
        # Basically locked for non-admins
        return self.locked_for_subscriptions or not self.bookable

    @property
    def duplicate_dict(self):
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
    def duplicate(self):
        return self.__class__(**self.duplicate_dict)

    def has_reservation(self, attendee_id):
        return self.subscriptions.filter_by(
            attendee_id=attendee_id).first() is not None

    def excluded_subscribers(
            self,
            year=None,
            as_uids=True,
            exclude_inactive=True
    ):
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

    def possible_subscribers(
            self,
            external_only=False,
            year=None,
            as_uids=False,
            exclude_inactive=True,
            auth_attendee=None
    ):
        """Returns the list of possible bookers. Attendees that already have
        a subscription for the parent course in the same year are excluded."""
        session = object_session(self)

        excl = self.excluded_subscribers(year, exclude_inactive)
        excl = excl.subquery('excl')

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

        query = query.filter(CourseAttendee.id.notin_(excl))

        if not as_uids:
            query = query.order_by(
                CourseAttendee.last_name, CourseAttendee.first_name)
        return query

    @property
    def email_recipients(self):
        return (att.email for att in self.attendees)

    def as_ical(self, event_url=None):
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

    def as_ical_attachment(self, url=None):
        return Attachment(
            filename=self.name.lower().replace(' ', '_') + '.ics',
            content=self.as_ical(url),
            content_type='text/calendar'
        )

    def can_book(self, attendee_or_id, year=None):
        att_id = attendee_or_id
        if isinstance(attendee_or_id, CourseAttendee):
            att_id = attendee_or_id.id
        for entry in self.excluded_subscribers(year, as_uids=True).all():
            if str(entry.id) == str(att_id):
                return False
        return True
