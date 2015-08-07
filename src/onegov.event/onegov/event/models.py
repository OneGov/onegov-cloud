from datetime import datetime
from dateutil import rrule
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from sedate import standardize_date, to_timezone
from sqlalchemy import Column, Enum, ForeignKey, Text, String
from sqlalchemy.orm import backref, relationship
from uuid import uuid4


class OccurrenceMixin(object):
    """ Contains all attributes events and ocurrences share. """

    #: title of the event
    title = Column(Text, nullable=False)

    #: description of the location of the event
    location = Column(Text, nullable=True)

    #: tags (categories) of the event
    tags = Column(Text, nullable=True)

    #: start date/time of the event (of the first event if recurring); no
    #  timezone here, it's UTC
    start = Column(UTCDateTime, nullable=False)

    #: end date/time of the event (of the first event if recurring); no
    #  timezone here, it's UTC
    end = Column(UTCDateTime, nullable=False)

    #: timezone the event was submitted
    timezone = Column(String, nullable=False)

    def display_start(self, timezone=None):
        return to_timezone(self.start, timezone or self.timezone)

    def display_end(self, timezone=None):
        return to_timezone(self.end, timezone or self.timezone)


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
        if name in ('state', 'title', 'location', 'tags',
                    'start', 'end', 'timezone', 'recurrence'):
            self._update_occurrences()

    def _update_occurrences(self):
        # clear old occurrences
        self.occurrences = []

        # do not create occurrences unless the event is published
        if not self.state == 'published':
            return

        if self.recurrence:
            # create all occurrences for this and next year
            max_year = datetime.today().year + 1
            for start in rrule.rrulestr(self.recurrence,
                                        dtstart=self.start):
                start = standardize_date(start, self.timezone)
                if start.year > max_year:
                    break
                end = start + (self.end - self.start)
                self.occurrences.append(
                    Occurrence(
                        title=self.title,
                        location=self.location,
                        tags=self.tags,
                        start=start,
                        end=end,
                        timezone=self.timezone
                    )
                )
        else:
            # create one occurence
            self.occurrences.append(
                Occurrence(
                    title=self.title,
                    location=self.location,
                    tags=self.tags,
                    start=self.start,
                    end=self.end,
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


class Occurrence(Base, OccurrenceMixin, TimestampMixin):
    """ Defines an occurrence of an event. """

    __tablename__ = 'event_occurrences'

    #: the internal number of the occurence
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the event this occurrence belongs to
    event_id = Column(UUID, ForeignKey(Event.id), nullable=False)
