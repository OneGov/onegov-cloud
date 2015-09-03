import icalendar

from datetime import datetime
from dateutil import rrule
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from sedate import standardize_date, to_timezone
from sqlalchemy import Column, Enum, ForeignKey, Text, String
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship
from uuid import uuid4


class OccurrenceMixin(object):
    """ Contains all attributes events and ocurrences share.

    The ``start`` and ``end`` date and times are stored in UTC - that is, they
    are stored internally without a timezone and are converted to UTC when
    getting or setting, see :class:`UTCDateTime`. Use the properties
    ``localized_start`` and ``localized_end`` to get the localized version of
    the date and times.
    """

    #: title of the event
    title = Column(Text, nullable=False)

    #: a nice id for the url, readable by humans
    name = Column(Text)

    #: description of the location of the event
    location = Column(Text, nullable=True)

    #: tags (categories) of the event
    _tags = Column(MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    @property
    def tags(self):
        return list(self._tags.keys()) if self._tags else []

    @tags.setter
    def tags(self, value):
        self._tags = dict(((key.strip(), '') for key in value))

    #: timezone of the event
    timezone = Column(String, nullable=False)

    #: start date and time of the event (of the first event if recurring)
    start = Column(UTCDateTime, nullable=False)

    @property
    def localized_start(self):
        return to_timezone(self.start, self.timezone)

    #: end date and time of the event (of the first event if recurring)
    end = Column(UTCDateTime, nullable=False)

    @property
    def localized_end(self):
        return to_timezone(self.end, self.timezone)

    def as_ical(self, description=None, rrule=None):
        """ Returns the occurrence as iCalendar string. """

        event = icalendar.Event()
        event.add('summary', self.title)
        event.add('dtstart', self.localized_start)
        event.add('dtend', self.localized_end)
        event.add('last-modified',
                  self.modified or self.created or datetime.utcnow())
        event['location'] = icalendar.vText(self.location)
        if description:
            event['description'] = icalendar.vText(description)
        if rrule:
            event['rrule'] = icalendar.vRecur(
                icalendar.vRecur.from_ical(rrule.replace('RRULE:', ''))
            )

        cal = icalendar.Calendar()
        cal.add('prodid', '-//OneGov//onegov.event//')
        cal.add('version', '2.0')
        cal.add_component(event)

        return cal.to_ical()


class Event(Base, OccurrenceMixin, ContentMixin, TimestampMixin):
    """ Defines an event.

    Occurrences are stored in a seperate table containing only a minimal set
    of attributes from the event. This could also be archieved using postgres
    directly with dateutil/plpythonu/pg_rrule and materialized views.

    Occurrences are only created/updated, if the event is published.
    Occurrences are created only for this and the next year.
    """

    __tablename__ = 'events'

    #: the internal number of the event
    id = Column(UUID, primary_key=True, default=uuid4)

    #: state of the event
    state = Column(
        Enum('initiated', 'submitted', 'published', 'withdrawn',
             name='event_state'),
        nullable=False,
        default='initiated'
    )

    #: recurrence of the event (RRULE, see RFC2445)
    recurrence = Column(Text, nullable=True)

    #: occurences of this event
    occurrences = relationship(
        "Occurrence",
        cascade="all, delete-orphan",
        backref=backref("event"),
        lazy='joined',
    )

    def __setattr__(self, name, value):
        super(Event, self).__setattr__(name, value)
        if name in ('state', 'title', 'name', 'location', 'tags',
                    'start', 'end', 'timezone', 'recurrence'):
            self._update_occurrences()

    def occurrence_dates(self, limit=True, localize=False):
        """ Returns the start dates of all occurrences.

        Returns non-localized dates per default. Limits the occurrences per
        default to this and the next year.
        """
        occurrences = [self.start]
        if self.recurrence:
            occurrences = rrule.rrulestr(self.recurrence, dtstart=self.start)
            occurrences = list(
                map(lambda x: standardize_date(x, self.timezone), occurrences)
            )
            if localize:
                occurrences = list(map(
                    lambda x: to_timezone(x, self.timezone), occurrences
                ))
            if limit:
                max_year = datetime.today().year + 1
                occurrences = list(
                    filter(lambda x: x.year <= max_year, occurrences)
                )
        return occurrences

    def _update_occurrences(self):
        # clear old occurrences
        self.occurrences = []

        # do not create occurrences unless the event is published
        if not self.state == 'published':
            return

        # do not create occurrences unless start and end is set
        if not self.start or not self.end:
            return

        # create all occurrences for this and next year
        for start in self.occurrence_dates():
            end = start + (self.end - self.start)
            name = '{0}-{1}'.format(self.name, start.date().isoformat())
            self.occurrences.append(
                Occurrence(
                    title=self.title,
                    name=name,
                    location=self.location,
                    tags=self.tags,
                    start=start,
                    end=end,
                    timezone=self.timezone
                )
            )

    def submit(self):
        assert self.state == 'initiated'
        self.state = 'submitted'

    def publish(self):
        assert self.state == 'submitted' or self.state == 'withdrawn'
        self.state = 'published'

    def withdraw(self):
        assert self.state == 'published'
        self.state = 'withdrawn'

    @property
    def description(self):
        return self.content.get('description', '')

    def as_ical(self):
        """ Returns the event and all its occurrences as iCalendar string. """

        return super(Event, self).as_ical(
            description=self.description,
            rrule=self.recurrence
        )


class Occurrence(Base, OccurrenceMixin, TimestampMixin):
    """ Defines an occurrence of an event. """

    __tablename__ = 'event_occurrences'

    #: the internal number of the occurence
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the event this occurrence belongs to
    event_id = Column(UUID, ForeignKey(Event.id), nullable=False)

    def as_ical(self):
        """ Returns the occurrence as iCalendar string. """

        return super(Occurrence, self).as_ical(
            description=self.event.description
        )
