from datetime import datetime
from dateutil import rrule
from dateutil.rrule import rrulestr
from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from icalendar import vRecur
from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.event.models.mixins import OccurrenceMixin
from onegov.event.models.occurrence import Occurrence
from onegov.file import File
from onegov.gis import CoordinatesMixin
from onegov.search import ORMSearchable
from pytz import UTC
from sedate import standardize_date
from sedate import to_timezone
from sqlalchemy import and_
from sqlalchemy import Column
from sqlalchemy import desc
from sqlalchemy import Enum
from sqlalchemy import func
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from uuid import uuid4


class EventFile(File):
    __mapper_args__ = {'polymorphic_identity': 'eventfile'}


class Event(Base, OccurrenceMixin, ContentMixin, TimestampMixin,
            ORMSearchable, CoordinatesMixin):
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
    description = content_property()

    #: the event organizer
    organizer = content_property()

    #: the source of the event, if imported
    source = meta_property()

    #: Recurrence of the event (RRULE, see RFC2445)
    recurrence = Column(Text, nullable=True)

    #: The associated image
    image = associated(EventFile, 'image', 'one-to-one', uselist=False)

    #: Recurrence of the event as icalendar object
    @property
    def icalendar_recurrence(self):
        if not self.recurrence:
            return None
        return vRecur.from_ical(self.recurrence.replace('RRULE:', ''))

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
    def es_skip(self):
        return self.state == 'submitted' or self.state == 'withdrawn'

    def source_url(self, request):
        """ Returns an url pointing to the external event if imported. """
        if not self.source:
            return None

        if self.source.startswith('guidle'):
            guidle_id = self.source.split('-')[-1].split('.')[0]

            return f"https://www.guidle.com/angebote/{guidle_id}"

    def __setattr__(self, name, value):
        """ Automatically update the occurrences if shared attributes change.
        """

        super().__setattr__(name, value)
        if name in ('state', 'title', 'name', 'location', 'tags',
                    'start', 'end', 'timezone', 'recurrence'):
            self._update_occurrences()

    @property
    def latest_occurrence(self):
        """ Returns the occurrence which is presently occurring, the next
        one to occur or the last occurrence.

        """

        session = object_session(self)

        base = session.query(Occurrence).filter_by(event_id=self.id)

        current = base.filter(and_(
            Occurrence.start <= func.now(),
            Occurrence.end >= func.now()
        )).order_by(Occurrence.start).limit(1)

        future = base.filter(
            Occurrence.start >= func.now()
        ).order_by(Occurrence.start).limit(1)

        past = base.filter(
            Occurrence.end <= func.now()
        ).order_by(desc(Occurrence.start))

        return current.union_all(future, past).first()

    @validates('recurrence')
    def validate_recurrence(self, key, r):
        """ Our rrules are quite limited in their complexity. This validator
        makes sure that is actually the case.

        This is a somewhat harsh limit, but it mirrors the actual use of
        onegov.event at this point. More complex rrules are not handled by the
        UI, nor is there currently a plan to do so.

        Currently supported are weekly recurrences and lists of rdates.

        The rational is that people commonly add recurring events on a weekly
        basis (which is a lot of work for a whole year). Or on a monthly
        or yearly basis, in which case selection of single dates is
        acceptable, or even preferrable to complex rrules.

        This UI talk doesn't belong into a module of course, but it is again
        a reailty that only a strict subset of rules is handled and so we want
        to catch events which we cannot edit in our UI early if they are
        imported from outside.

        """
        if r:
            rule = rrulestr(r)

            # a rule must either have a frequency or be a list of rdates
            if not hasattr(rule, '_freq'):
                if all((l.startswith('RDATE') for l in r.splitlines())):
                    return r

                raise RuntimeError(f"'{r}' is too complex")

            # we also only do weekly recurrences (they can also be used
            # to do daily recurrences if they are set to include all days)
            if not rule._freq == rrule.WEEKLY:
                raise RuntimeError(f"The frequency of '{r}' is not WEEKLY")

            # we require a definite end
            if not getattr(rule, '_until'):
                raise RuntimeError(f"'{r}' has no UNTIL")

            # we also want the end date to be timezone-aware
            if rule._until.tzinfo is None:
                raise RuntimeError(f"'{r}''s UNTIL is not timezone-aware")

        return r

    def occurrence_dates(self, limit=True, localize=False):
        """ Returns the start dates of all occurrences.

        Returns non-localized dates per default. Limits the occurrences per
        default to this and the next year.
        """

        def to_local(dt, timezone):
            if dt.tzinfo:
                return to_timezone(dt, timezone).replace(tzinfo=None)
            return dt

        dates = [self.start]
        if self.recurrence:
            # Make sure the RRULE uses local dates (or else the DST is wrong)
            start_local = to_local(self.start, self.timezone)
            try:
                rule = rrulestr(self.recurrence, dtstart=self.start)
                if getattr(rule, '_dtstart', None):
                    rule._dtstart = to_local(rule._dtstart, self.timezone)
                if getattr(rule, '_until', None):
                    rule._until = to_local(rule._until, self.timezone)
                rule = rrulestr(str(rule))
            except ValueError:
                # This might happen if only RDATEs and EXDATEs are present
                rule = rrulestr(self.recurrence, dtstart=start_local)

            # Make sure, the RDATEs and EXDATEs contain the start times
            for attribute in ('_exdate', '_rdate'):
                if hasattr(rule, attribute):
                    setattr(rule, attribute, [
                        to_local(date_, self.timezone).replace(
                            hour=start_local.hour, minute=start_local.minute
                        )
                        for date_ in getattr(rule, attribute)
                    ])

            # Generate the occurences and convert to UTC
            dates = [standardize_date(date_, self.timezone) for date_ in rule]

            # Make sure the start date is port of the reucrrence
            if self.start not in dates:
                dates.append(self.start)
                dates.sort()

        if localize:
            dates = [to_timezone(date_, self.timezone) for date_ in dates]

        if limit:
            max_year = datetime.today().year + 1
            dates = [date_ for date_ in dates if date_.year <= max_year]

        return dates

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
                    timezone=self.timezone
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

        modified = self.modified or self.created or datetime.utcnow()

        vevent = vEvent()
        vevent.add('uid', f'{self.name}@onegov.event')
        vevent.add('summary', self.title)
        vevent.add('dtstart', to_timezone(self.start, UTC))
        vevent.add('dtend', to_timezone(self.end, UTC))
        vevent.add('last-modified', modified)
        vevent.add('dtstamp', modified)
        vevent.add('location', self.location)
        vevent.add('description', self.description)
        vevent.add('categories', self.tags)
        if self.recurrence:
            vevent.add('rrule', self.icalendar_recurrence)
        if url:
            vevent.add('url', url)
        if self.coordinates:
            vevent.add('geo', (self.coordinates.lat, self.coordinates.lon))

        vcalendar = vCalendar()
        vcalendar.add('prodid', '-//OneGov//onegov.event//')
        vcalendar.add('version', '2.0')
        vcalendar.add_component(vevent)
        return vcalendar.to_ical()
