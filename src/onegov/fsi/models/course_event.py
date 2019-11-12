import datetime
from collections import OrderedDict
from uuid import uuid4

from sedate import utcnow
from sqlalchemy import Column, Boolean, SmallInteger, \
    Enum, Text, Interval, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.notification_template import InfoTemplate, \
    ReservationTemplate, CancellationTemplate, ReminderTemplate
from onegov.fsi.models.reservation import reservation_table
from onegov.fsi import _

COURSE_EVENT_STATUSES = ('created', 'confirmed', 'canceled', 'planned')
COURSE_EVENT_STATUSES_TRANSLATIONS = (
    _('Created'), _('Confirmed'), _('Canceled'), _('Planned'))


# for forms...
def course_status_choices():
    return tuple(
        (val, key) for val, key in zip(COURSE_EVENT_STATUSES,
                                       COURSE_EVENT_STATUSES_TRANSLATIONS))


class CourseEvent(Base, TimestampMixin):

    default_reminder_before = datetime.timedelta(days=7)

    __tablename__ = 'fsi_course_events'
    __table_args__ = (UniqueConstraint('name', 'start', 'end',
                                       name='_name_ts_uc'),)

    id = Column(UUID, primary_key=True, default=uuid4)

    name = Column(Text, nullable=False)
    # Long description
    description = Column(Text, nullable=False)

    # Event specific information
    start = Column(UTCDateTime, nullable=False)
    end = Column(UTCDateTime, nullable=False)
    presenter_name = Column(Text, nullable=False)
    presenter_company = Column(Text, nullable=False)
    min_attendees = Column(SmallInteger, nullable=False, default=1)
    max_attendees = Column(SmallInteger, nullable=True)
    refresh_interval = Column(Interval, nullable=True)

    # If the course has to be refreshed after some interval
    mandatory_refresh = Column(Boolean, nullable=False, default=False)

    # Creator of this course event
    # user_id = Column(UUID, ForeignKey('users.id'), nullable=True)

    status = Column(
        Enum(
            *COURSE_EVENT_STATUSES, name='status'
        ),
        nullable=False, default='created')

    attendees = relationship(
        CourseAttendee,
        secondary=reservation_table,
        primaryjoin=id == reservation_table.c.course_event_id,
        secondaryjoin=reservation_table.c.attendee_id
        == CourseAttendee.id,
        lazy='dynamic'
    )

    reservations = relationship(
        'Reservation',
        backref=backref(
            'course_event',
            lazy='joined'
        ),
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    notification_templates = relationship('FsiNotificationTemplate',
                                          back_populates='course_event')

    # The associated notification templates
    info_template = relationship("InfoTemplate", uselist=False)
    reservation_template = relationship("ReservationTemplate", uselist=False)
    cancellation_template = relationship("CancellationTemplate", uselist=False)
    reminder_template = relationship("ReminderTemplate", uselist=False)

    # hides from member roles
    hidden_from_public = Column(Boolean, nullable=False, default=False)

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
        return self.start - self.schedule_reminder_before

    @hybrid_property
    def next_event_start(self):
        return self.end + self.refresh_interval

    @property
    def duration(self):
        return self.end - self.start

    @property
    def hidden(self):
        # Add criteria when a course should be hidden based on status or attr
        return self.hidden_from_public

    @property
    def available_seats(self):
        if self.max_attendees:
            seats = self.max_attendees - self.reservations.count()
            return 0 if seats < 0 else seats
        return None

    @property
    def booked(self):
        return self.max_attendees <= self.reservations.count()

    @property
    def bookable(self):
        return not self.booked and self.start > utcnow()

    @property
    def is_past(self):
        return self.start < utcnow()

    @property
    def duplicate_dict(self):
        return OrderedDict(
            name=self.name, description=self.description,
            presenter_name=self.presenter_name,
            presenter_company=self.presenter_company,
            min_attendees=self.min_attendees,
            max_attendees=self.max_attendees,
            mandatory_refresh=self.mandatory_refresh,
            refresh_interval=self.refresh_interval,
            status='created',
            hidden_from_public=self.hidden_from_public
        )

    @property
    def duplicate(self):
        return self.__class__(**self.duplicate_dict)

    def send_reminder_mail(self):
        # use self.attendees to get a list of emails
        raise NotImplementedError

    def cancel_reservation(self, reservation):
        self.reservations.remove(reservation)
