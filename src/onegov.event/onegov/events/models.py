from datetime import datetime
from dateutil import rrule
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.ticket import handlers
from onegov.user.model import User
from sqlalchemy import Column, Enum, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, deferred, relationship, object_session
from uuid import uuid4


class Event(Base, TimestampMixin):
    """ Defines an event.

    Occurrences are stored in a seperate table containing only a minimal set
    of attributes from the event. This could also be archieved using postgres
    directly with dateutil/plpythonu/pg_rrule and materialized views.

    Occurrences are only created/updated, if the event is published.
    Occurrences are created only for this and the next year.
    """

    # todo: Should we store location information such as coordinates here or as
    #       a more general concept elsewhere?
    #       coordiantes = Column(JSON, nullable=True)

    # todo: Should we store some meta information, such as the submitter of
    #       this event?

    # todo: Should we limit the start-end diff? Maybe two days?

    # todo: add getter/setter for start/end which returns/accepts datetimes
    #       with timezone information?

    # todo: Add attachments

    # todo: Add images

    # todo: Should we copy title, description, tags, location (description and
    #       coordinates), datetimes & timezones as well?

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

    #: title of the event
    title = Column(Text, nullable=False)

    #: description of the event
    description = Column(Text, nullable=True)

    #: description of the location of the event
    location = Column(Text, nullable=True)

    #: tags (categories) of the event
    tags = Column(Text, nullable=True, name='tags')

    #: start date/time of the event (of the first event if recurring); no
    #  timezone here, it's UTC
    start = Column(DateTime, nullable=False, name='start')

    #: end date/time of the event (of the first event if recurring); no
    #  timezone here, it's UTC
    end = Column(DateTime, nullable=False, name='end')

    #: recurrence of the event (RRULE, see RFC2445)
    recurrence = Column(Text, nullable=True, name='recurrence')

    #: occurences of this event
    occurrences = relationship(
        "Occurrence",
        cascade="all, delete-orphan",
        backref=backref("event"),
        lazy='joined',
        # order_by="Occurence.group",
    )

    def __setattr__(self, name, value):
        super(Event, self).__setattr__(name, value)

        # Update occurrences
        if name in ('state', 'start', 'end', 'recurrence', 'tags'):
            # clear old occurrences
            self.occurrences.clear()

            # do not create occurrences unless the event is published
            if not self.state == 'published':
                return

            if self.recurrence:
                # create all occurrences for this and next year
                max_year = datetime.today().year + 1
                for start in rrule.rrulestr(self.recurrence,
                                            dtstart=self.start):
                    if start.year > max_year:
                        break
                    end = start + (self.end - self.start)
                    self.occurrences.append(
                        Occurrence(start=start, end=end, tags=self.tags)
                    )
            else:
                # create one occurence
                self.occurrences.append(
                    Occurrence(start=self.start, end=self.end, tags=self.tags)
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


class Occurrence(Base, TimestampMixin):
    """ Defines an occurrence of an event. """

    __tablename__ = 'event_occurrences'

    #: the internal number of the occurence
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the event this occurrence belongs to
    event_id = Column(UUID, ForeignKey(Event.id), nullable=False)

    #: start date/time of the event
    start = Column(DateTime, nullable=True)

    #: end date/time of the event
    end = Column(DateTime, nullable=True)

    #: tags (categories) of the event
    tags = Column(Text, nullable=True)
