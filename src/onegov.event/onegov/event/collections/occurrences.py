from cached_property import cached_property
from datetime import date
from datetime import datetime
from datetime import timedelta
from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from onegov.core.collection import Pagination
from onegov.core.utils import get_unique_hstore_keys
from onegov.event.models import Event
from onegov.event.models import Occurrence
from pytz import UTC
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sedate import to_timezone
from sqlalchemy import and_
from sqlalchemy import distinct
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import array


class OccurrenceCollection(Pagination):
    """ Manages a list of occurrences.

    Occurrences are read only (no ``add`` method here), they are generated
    automatically when adding a new event.

    Occurrences can be filtered by start and end dates as well as tags.

    By default, only current occurrences are returned.
    """

    def __init__(self, session, page=0, start=None, end=None, tags=None):
        self.session = session
        self.page = page
        self.start = start
        self.end = end
        self.tags = tags if tags else []

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session, index, self.start, self.end, self.tags
        )

    def for_filter(self, **kwargs):
        """ Returns a new instance of the collection.

        Copies the current filters if not specified. Also adds or removes a
        single tag if given.
        """

        start = kwargs['start'] if 'start' in kwargs else self.start
        end = kwargs['end'] if 'end' in kwargs else self.end
        tags = kwargs['tags'] if 'tags' in kwargs else list(self.tags)

        if 'tag' in kwargs:
            tag = kwargs['tag']
            if tag in tags:
                tags.remove(tag)
            elif tag is not None:
                tags.append(tag)

        return self.__class__(self.session, 0, start, end, tags)

    @cached_property
    def used_timezones(self):
        """ Returns a list of all the timezones used by the occurrences. """

        return [
            tz[0] for tz in self.session.query(distinct(Occurrence.timezone))
        ]

    @cached_property
    def used_tags(self):
        """ Returns a list of all the tags used by the occurrences.

        This could be solve possibly more effienciently with the skey function
        currently not supported by SQLAlchemy (e.g.
        ``select distinct(skeys(tags))``), see
        http://stackoverflow.com/q/12015942/3690178

        """

        return get_unique_hstore_keys(self.session, Occurrence._tags)

    def query(self, outdated=False):
        """ Queries occurrences with the set parameters.

        Finds all occurrences with any of the set tags and within the set
        start and end date. Start and end date are assumed to be dates only and
        therefore without a timezone - we search for the given date in the
        timezone of the occurrence!.

        If no start date is set and ``outdated`` is not set, only current
        occurrences are returned.
        """

        query = self.session.query(Occurrence)

        if self.start is not None:
            assert type(self.start) is date
            start = as_datetime(self.start)

            expressions = []
            for timezone in self.used_timezones:
                localized_start = replace_timezone(start, timezone)
                localized_start = standardize_date(localized_start, timezone)
                expressions.append(
                    and_(
                        Occurrence.timezone == timezone,
                        Occurrence.start >= localized_start
                    )
                )

            query = query.filter(or_(*expressions))
        elif not outdated:
            start = as_datetime(date.today())

            expressions = []
            for timezone in self.used_timezones:
                localized_start = replace_timezone(start, timezone)
                localized_start = standardize_date(localized_start, timezone)
                expressions.append(
                    and_(
                        Occurrence.timezone == timezone,
                        Occurrence.start >= localized_start
                    )
                )

            query = query.filter(or_(*expressions))

        if self.end is not None:
            assert type(self.end) is date
            end = as_datetime(self.end)
            end = end + timedelta(days=1)

            expressions = []
            for timezone in self.used_timezones:
                localized_end = replace_timezone(end, timezone)
                localized_end = standardize_date(localized_end, timezone)
                expressions.append(
                    and_(
                        Occurrence.timezone == timezone,
                        Occurrence.end < localized_end
                    )
                )

            query = query.filter(or_(*expressions))

        if self.tags:
            query = query.filter(Occurrence._tags.has_any(array(self.tags)))

        query = query.order_by(Occurrence.start, Occurrence.title)

        return query

    def by_name(self, name):
        """ Returns an occurrence by its URL-friendly name.

        The URL-friendly name is automatically constructed as follows:

        ``unique name of the event``-``date of the occurrence``

        e.g.

        ``squirrel-park-visit-6-2015-06-20``

        """

        query = self.session.query(Occurrence).filter(Occurrence.name == name)
        return query.first()

    def as_ical(self, request):
        """ Returns the the events of the given occurrences as iCalendar
        string.

        """

        vcalendar = vCalendar()
        vcalendar.add('prodid', '-//OneGov//onegov.event//')
        vcalendar.add('version', '2.0')

        query = self.query().with_entities(Occurrence.event_id)
        event_ids = set([r.event_id for r in query])
        query = self.session.query(Event).filter(Event.id.in_(event_ids))
        for event in query:
            modified = event.modified or event.created or datetime.utcnow()

            vevent = vEvent()
            vevent.add('uid', f'{event.name}@onegov.event')
            vevent.add('summary', event.title)
            vevent.add('dtstart', to_timezone(event.start, UTC))
            vevent.add('dtend', to_timezone(event.end, UTC))
            vevent.add('last-modified', modified)
            vevent.add('dtstamp', modified)
            vevent.add('location', event.location)
            vevent.add('description', event.description)
            vevent.add('categories', event.tags)
            if event.recurrence:
                vevent.add('rrule', event.icalendar_recurrence)
            if event.coordinates:
                vevent.add(
                    'geo', (event.coordinates.lat, event.coordinates.lon)
                )
            vevent.add('url', request.link(event))
            vcalendar.add_component(vevent)

        return vcalendar.to_ical()
