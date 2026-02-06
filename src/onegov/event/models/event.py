from __future__ import annotations

from datetime import datetime, timedelta
from dateutil import rrule
from dateutil.rrule import rrulestr
from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from icalendar import vRecur
from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.event.models.mixins import OccurrenceMixin
from onegov.event.models.occurrence import Occurrence
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.gis import Coordinates
from onegov.gis import CoordinatesMixin
from onegov.search import SearchableContent
from PIL.Image import DecompressionBombError
from pytz import UTC
from sedate import standardize_date
from sedate import to_timezone, utcnow
from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from sqlalchemy.orm.attributes import set_committed_value
from translationstring import TranslationString
from uuid import uuid4


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator
    from onegov.core.orm.mixins import dict_property
    from onegov.core.request import CoreRequest
    from sqlalchemy.orm import Query
    from typing import Literal
    from typing import TypeAlias

    EventState: TypeAlias = Literal[
        'initiated',
        'submitted',
        'published',
        'withdrawn'
    ]


class EventFile(File):
    __mapper_args__ = {'polymorphic_identity': 'eventfile'}


class Event(Base, OccurrenceMixin, TimestampMixin, SearchableContent,
            CoordinatesMixin):
    """ Defines an event.

    Occurrences are stored in a seperate table containing only a minimal set
    of attributes from the event. This could also be archieved using postgres
    directly with dateutil/plpythonu/pg_rrule and materialized views.

    Occurrences are only created/updated, if the event is published.
    Occurrences are created only for this and the next year.
    """

    __tablename__ = 'events'

    occurrence_dates_year_limit = 2

    #: Internal number of the event
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: State of the event
    state: Column[EventState] = Column(
        Enum(  # type: ignore[arg-type]
            'initiated', 'submitted', 'published', 'withdrawn',
            name='event_state'
        ),
        nullable=False,
        default='initiated'
    )

    #: description of the event
    description: dict_property[str | None] = content_property()

    #: the event organizer
    organizer: dict_property[str | None] = content_property()

    #: the event organizer's public e-mail address
    organizer_email: dict_property[str | None] = content_property()

    #: the event organizer's phone number
    organizer_phone: dict_property[str | None] = content_property()

    #: an external url for the event
    external_event_url: dict_property[str | None] = content_property()

    #: an external url for the event
    event_registration_url: dict_property[str | None] = content_property()

    #: the price of the event (a text field, not an amount)
    price: dict_property[str | None] = content_property()

    #: the source of the event, if imported
    source: dict_property[str | None] = meta_property()

    #: when the source of the event was last updated (if imported)
    source_updated: dict_property[str | None] = meta_property()

    #: Recurrence of the event (RRULE, see RFC2445)
    recurrence: Column[str | None] = Column(Text, nullable=True)

    #: The access property of the event, taken from onegov.org. Not ideal to
    #: have this defined here, instead of using an AccessExtension, but that
    #: would only be possible with deeper changes to the Event model.
    access: dict_property[str] = meta_property(default='public')

    #: The associated image
    image = associated(
        EventFile, 'image', 'one-to-one', uselist=False, backref_suffix='image'
    )

    #: The associated PDF
    pdf = associated(
        EventFile, 'pdf', 'one-to-one', uselist=False, backref_suffix='pdf'
    )

    def set_image(
        self,
        content: bytes | IO[bytes] | None,
        filename: str | None = None
    ) -> None:

        self.set_blob('image', content, filename)

    def set_pdf(
        self,
        content: bytes | IO[bytes] | None,
        filename: str | None = None
    ) -> None:

        self.set_blob('pdf', content, filename)

    def set_blob(
        self,
        blob: str,
        content: bytes | IO[bytes] | None,
        filename: str | None = None
    ) -> None:
        """ Adds or removes the given blob. """

        filename = filename or 'file'

        if not content:
            setattr(self, blob, None)

        elif getattr(self, blob):
            getattr(self, blob).reference = as_fileintent(content, filename)

        else:
            try:
                setattr(self, blob, EventFile(  # type: ignore[misc]
                    name=filename,
                    reference=as_fileintent(content, filename)
                ))
            except DecompressionBombError:
                setattr(self, blob, None)

    #: Occurrences of the event
    occurrences: relationship[list[Occurrence]] = relationship(
        'Occurrence',
        cascade='all, delete-orphan',
        back_populates='event',
        lazy='joined',
    )

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString('Events', domain='onegov.org')
    fts_title_property = 'title'
    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'description': {'type': 'localized', 'weight': 'B'},
        'location': {'type': 'localized', 'weight': 'B'},
        'organizer': {'type': 'localized', 'weight': 'B'},
        # FIXME: Should we move this to fts_tags?
        'filter_keywords': {'type': 'keyword', 'weight': 'A'}
    }

    @property
    def fts_public(self) -> bool:
        return self.state == 'published'

    @property
    def fts_skip(self) -> bool:
        return self.state != 'published' or getattr(self, '_es_skip', False)

    @property
    def fts_last_change(self) -> datetime:
        latest = self.latest_occurrence
        if latest is None:
            # NOTE: if there are no occurrences at all we want to deprioritize
            #       this by a lot, so we pretend the latest occurrence was four
            #       years ago, which results in a factor of around 8%
            return utcnow() - timedelta(days=1461)
        elif latest.start < utcnow():
            # NOTE: if the occurrence is in the past, we want to deprioritize
            #       it over upcoming events, we use a gaussian time decay so
            #       being in the future by x days would be deprioritized the
            #       same as being in the past by x days, so we subtract one
            #       year to make past events less relevant. For an event that
            #       just happened this results in a factor of around 85%, so
            #       still relevant, but not as relevant as the upcoming events.
            return latest.start - timedelta(days=365)
        return latest.start

    def source_url(self, request: CoreRequest) -> str | None:
        """ Returns an url pointing to the external event if imported. """
        if not self.source or not self.source.startswith('guidle'):
            return None

        guidle_id = self.source.rsplit('-', 1)[-1].split('.', 1)[0]
        return f'https://www.guidle.com/angebote/{guidle_id}'

    def __setattr__(self, name: str, value: object) -> None:
        """ Automatically update the occurrences if shared attributes change
        """

        # FIXME: This is insanely messy, since we delete and add all the
        #        occurrences for every attribute we change, for one, we
        #        could optimize this by only deleting existing occurences
        #        if occurence_dates no longer matches the existing
        #        occurrences, and we could do this only once at the end
        #        when the new state is flushed, instead of for every
        #        individual attribute change. An observer would probably
        #        get us there.
        super().__setattr__(name, value)
        if name in ('state', 'title', 'name', 'location', 'tags',
                    'filter_keywords', 'start', 'end', 'timezone',
                    'recurrence'):
            self._update_occurrences()

    @property
    def base_query(self) -> Query[Occurrence]:
        session = object_session(self)
        return session.query(Occurrence).filter_by(event_id=self.id)

    @property
    def latest_occurrence(self) -> Occurrence | None:
        """ Returns the occurrence which is presently occurring, the next
        one to occur or the last occurrence.

        """

        now = utcnow()
        base = self.base_query
        current = base.filter(and_(
            Occurrence.start <= now,
            Occurrence.end >= now
        )).order_by(Occurrence.start).limit(1)

        future = base.filter(
            Occurrence.start >= now
        ).order_by(Occurrence.start).limit(1)

        past = base.filter(
            Occurrence.end <= now
        ).order_by(desc(Occurrence.start))

        return current.union_all(future, past).first()

    def future_occurrences(
        self,
        offset: int = 0,
        limit: int = 10
    ) -> Query[Occurrence]:

        return self.base_query.filter(
            Occurrence.start >= utcnow()
        ).order_by(Occurrence.start).offset(offset).limit(limit)

    @validates('recurrence')
    def validate_recurrence(self, key: str, r: str | None) -> str | None:
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
                if all(l.startswith('RDATE') for l in r.splitlines()):
                    return r

                raise RuntimeError(f"'{r}' is too complex")

            # we also only do weekly recurrences (they can also be used
            # to do daily recurrences if they are set to include all days)
            if not rule._freq == rrule.WEEKLY:
                raise RuntimeError(f"The frequency of '{r}' is not WEEKLY")

            # we require a definite end
            until: datetime | None = getattr(rule, '_until', None)
            if until is None:
                raise RuntimeError(f"'{r}' has no UNTIL")

            # we also want the end date to be timezone-aware
            if until.tzinfo is None:
                raise RuntimeError(f"'{r}''s UNTIL is not timezone-aware")

        return r

    def occurrence_dates(
        self,
        limit: bool = True,
        localize: bool = False
    ) -> list[datetime]:
        """ Returns the start dates of all occurrences.

        Returns non-localized dates per default. Limits the occurrences per
        default to this and the next year.
        """

        def to_local(dt: datetime, timezone: str) -> datetime:
            if dt.tzinfo:
                return to_timezone(dt, timezone).replace(tzinfo=None)
            return dt

        dates = [self.start]
        if self.recurrence:
            # Make sure the RRULE uses local dates (or else the DST is wrong)
            start_local = to_local(self.start, self.timezone)
            try:
                rule = rrulestr(self.recurrence, dtstart=self.start)
                if dtstart := getattr(rule, '_dtstart', None):
                    rule._dtstart = to_local(  # type: ignore[union-attr]
                        dtstart,
                        self.timezone
                    )
                if until := getattr(rule, '_until', None):
                    rule._until = to_local(until, self.timezone)  # type:ignore
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
            max_year = datetime.today().year + self.occurrence_dates_year_limit
            dates = [date_ for date_ in dates if date_.year <= max_year]

        return dates

    def spawn_occurrence(self, start: datetime) -> Occurrence:
        """ Create an occurrence at the given date, without storing it. """

        end = start + (self.end - self.start)
        name = f'{self.name}-{start.date().isoformat()}'

        return Occurrence(  # type:ignore[misc]
            title=self.title,
            name=name,
            location=self.location,
            tags=self.tags,
            filter_keywords=self.filter_keywords,
            start=start,
            end=end,
            timezone=self.timezone,
        )

    @property
    def virtual_occurrence(self) -> Occurrence:
        """ Before the event is accepted, there are no real occurrences stored
        in the database.

        At this time it is useful to be able to generate the latest occurence
        without storing it.

        """

        for start in self.occurrence_dates(limit=False):
            occurrence = self.spawn_occurrence(start)
            set_committed_value(occurrence, 'event', self)

            if session := object_session(occurrence):
                session.expunge(occurrence)
                session.flush()

            return occurrence

        raise AssertionError('unreachable')

    def _update_occurrences(self) -> None:
        """ Updates the occurrences.

        Removes all occurrences if the event is not published or no start and
        end date/time is set. Only occurrences for this and next year are
        created.
        """

        # clear old occurrences
        self.occurrences = []

        # do not create occurrences unless the event is published
        if self.state != 'published':
            return

        # do not create occurrences unless start and end is set
        if not self.start or not self.end:
            return

        # create all occurrences for this and next year
        for start in self.occurrence_dates():
            occ = self.spawn_occurrence(start)
            if session := object_session(self):
                session.add(occ)
            self.occurrences.append(occ)

        for occ in self.occurrences:
            occ.filter_keywords = self.filter_keywords

    def submit(self) -> None:
        """ Submit the event. """

        assert self.state == 'initiated'
        self.state = 'submitted'

    def publish(self) -> None:
        """ Publish the event.

        Publishing the event will generate the occurrences.
        """

        assert self.state == 'submitted' or self.state == 'withdrawn'
        self.state = 'published'

    def withdraw(self) -> None:
        """ Withdraw the event.

        Withdraw the event will delete the occurrences."""

        assert self.state in ('submitted', 'published')
        self.state = 'withdrawn'

    def get_ical_vevents(self, url: str | None = None) -> Iterator[vEvent]:
        """ Returns the event and all its occurrences as icalendar objects.

        If the calendar has a bunch of RDATE's instead of a proper RRULE, we
        return every occurrence as separate event since most calendars don't
        support RDATE's.

        """

        modified = self.modified or self.created or utcnow()
        rrule = None
        if self.recurrence:
            rrule = vRecur.from_ical(self.recurrence.replace('RRULE:', ''))

        for dtstart in self.occurrence_dates():
            dtstart = to_timezone(dtstart, UTC)
            dtend = dtstart + (self.end - self.start)
            vevent = vEvent()
            vevent.add('uid', f'{self.name}-{dtstart.date()}@onegov.event')
            vevent.add('summary', self.title)
            vevent.add('dtstart', dtstart)
            vevent.add('dtend', dtend)
            vevent.add('last-modified', modified)
            vevent.add('dtstamp', modified)
            vevent.add('location', self.location)
            vevent.add('description', self.description)
            vevent.add('categories', self.tags)
            if rrule:
                vevent.add('rrule', rrule)
            if url:
                vevent.add('url', url)
            if self.coordinates:
                assert isinstance(self.coordinates, Coordinates)
                vevent.add('geo', (self.coordinates.lat, self.coordinates.lon))
            yield vevent

            if rrule:
                break

    def as_ical(self, url: str | None = None) -> bytes:
        """ Returns the event and all its occurrences as iCalendar string.

        """
        vcalendar = vCalendar()
        vcalendar.add('prodid', '-//OneGov//onegov.event//')
        vcalendar.add('version', '2.0')
        for vevent in self.get_ical_vevents(url):
            vcalendar.add_component(vevent)
        return vcalendar.to_ical()
