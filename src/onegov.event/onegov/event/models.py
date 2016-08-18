import icalendar

from datetime import datetime
from dateutil import rrule
from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    content_property,
    ContentMixin,
    TimestampMixin
)
from onegov.core.orm.types import JSON, UUID, UTCDateTime
from onegov.search import ORMSearchable
from pytz import UTC
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

    #: Title of the event
    title = Column(Text, nullable=False)

    #: A nice id for the url, readable by humans
    name = Column(Text)

    #: Description of the location of the event
    location = Column(Text, nullable=True)

    #: Tags/Categories of the event
    _tags = Column(MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    @property
    def tags(self):
        """ Tags/Categories of the event. """

        return list(self._tags.keys()) if self._tags else []

    @tags.setter
    def tags(self, value):
        self._tags = dict(((key.strip(), '') for key in value))

    #: Timezone of the event
    timezone = Column(String, nullable=False)

    #: Start date and time of the event (of the first event if recurring)
    start = Column(UTCDateTime, nullable=False)

    @property
    def localized_start(self):
        """ The localized version of the start date/time. """

        return to_timezone(self.start, self.timezone)

    #: End date and time of the event (of the first event if recurring)
    end = Column(UTCDateTime, nullable=False)

    @property
    def localized_end(self):
        """ The localized version of the end date/time. """

        return to_timezone(self.end, self.timezone)

    #: The coordinates of the event
    coordinates = Column(JSON, nullable=True)

    @property
    def has_coordinates(self):
        if self.coordinates:
            return self.coordinates.get('lat') and self.coordinates.get('lon')
        else:
            return False

    @property
    def lat(self):
        return self.coordinates and self.coordinates.get('lat')

    @property
    def lon(self):
        return self.coordinates and self.coordinates.get('lon')

    @property
    def zoom(self):
        return self.coordinates and self.coordinates.get('zoom')

    def as_ical(self, description=None, rrule=None, url=None):
        """ Returns the occurrence as iCalendar string. """

        event = icalendar.Event()
        event.add('summary', self.title)
        event.add('dtstart', to_timezone(self.start, UTC))
        event.add('dtend', to_timezone(self.end, UTC))
        event.add('last-modified',
                  self.modified or self.created or datetime.utcnow())
        event['location'] = icalendar.vText(self.location)
        if description:
            event['description'] = icalendar.vText(description)
        if rrule:
            event['rrule'] = icalendar.vRecur(
                icalendar.vRecur.from_ical(rrule.replace('RRULE:', ''))
            )
        if url:
            event.add('url', url)

        cal = icalendar.Calendar()
        cal.add('prodid', '-//OneGov//onegov.event//')
        cal.add('version', '2.0')
        cal.add_component(event)

        return cal.to_ical()


class Event(Base, OccurrenceMixin, ContentMixin, TimestampMixin,
            ORMSearchable):
    """ Defines an event.

    Occurrences are stored in a seperate table containing only a minimal set
    of attributes from the event. This could also be archieved using postgres
    directly with dateutil/plpythonu/pg_rrule and materialized views.

    Occurrences are only created/updated, if the event is published.
    Occurrences are created only for this and the next year.
    """

    __tablename__ = 'events'

    #: Internal number of the event
    id = Column(UUID, primary_key=True, default=uuid4)

    #: State of the event
    state = Column(
        Enum('initiated', 'submitted', 'published', 'withdrawn',
             name='event_state'),
        nullable=False,
        default='initiated'
    )

    #: description of the event
    description = content_property('description')

    #: the event organizer
    organizer = content_property('organizer')

    #: Recurrence of the event (RRULE, see RFC2445)
    recurrence = Column(Text, nullable=True)

    #: Occurences of the event
    occurrences = relationship(
        "Occurrence",
        cascade="all, delete-orphan",
        backref=backref("event"),
        lazy='joined',
    )

    es_properties = {
        'title': {'type': 'localized'},
        'description': {'type': 'localized'},
        'location': {'type': 'localized'},
        'organizer': {'type': 'localized'}
    }

    @property
    def es_public(self):
        return self.state == 'published'

    @property
    def es_language(self):
        return 'de'  # XXX add to database in the future

    def __setattr__(self, name, value):
        """ Automatically update the occurrences if shared attributes change.
        """

        super().__setattr__(name, value)
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
        """ Updates the occurrences.

        Removes all occurrences if the event is not published or no start and
        end date/time is set. Only occurrences for this and next year are
        created.
        """

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
                    timezone=self.timezone,
                    coordinates=self.coordinates,
                )
            )

    def submit(self):
        """ Submit the event. """

        assert self.state == 'initiated'
        self.state = 'submitted'

    def publish(self):
        """ Publish the event.

        Publishing the event will generate the occurrences.
        """

        assert self.state == 'submitted' or self.state == 'withdrawn'
        self.state = 'published'

    def withdraw(self):
        """ Withdraw the event.

        Withdraw the event will delete the occurrences."""

        assert self.state == 'published'
        self.state = 'withdrawn'

    def as_ical(self, url=None):
        """ Returns the event and all its occurrences as iCalendar string. """

        return super().as_ical(
            description=self.description,
            rrule=self.recurrence,
            url=url
        )


class Occurrence(Base, OccurrenceMixin, TimestampMixin):
    """ Defines an occurrence of an event. """

    __tablename__ = 'event_occurrences'

    #: Internal number of the occurence
    id = Column(UUID, primary_key=True, default=uuid4)

    #: Event this occurrence belongs to
    event_id = Column(UUID, ForeignKey(Event.id), nullable=False)

    def as_ical(self, url=None):
        """ Returns the occurrence as iCalendar string. """

        return super().as_ical(
            description=self.event.description,
            url=url
        )
