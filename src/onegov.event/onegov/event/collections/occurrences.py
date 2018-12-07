from cached_property import cached_property
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from icalendar import Calendar as vCalendar
from onegov.core.collection import Pagination
from onegov.core.utils import get_unique_hstore_keys
from onegov.event.models import Event
from onegov.event.models import Occurrence
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sqlalchemy import and_
from sqlalchemy import distinct
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import array


class OccurrenceCollection(Pagination):
    """ Manages a list of occurrences.

    Occurrences are read only (no ``add`` method here), they are generated
    automatically when adding a new event.

    Occurrences can be filtered by relative date ranges (``today``,
    ``tomorrow``, ``weekend``, ``week``, ``month``) or by a given start date
    and/or end date. The range filter is dominant and overwrites the start and
    end dates if provided.

    By default, only current occurrences are used.

    Occurrences can be additionally filtered by tags.

    """

    date_ranges = ('today', 'tomorrow', 'weekend', 'week', 'month')

    def __init__(
        self, session, page=0,
        range=None, start=None, end=None, outdated=False,
        tags=None
    ):
        self.session = session
        self.page = page
        self.range = range if range in self.date_ranges else None
        self.start, self.end = self.range_to_dates(range, start, end)
        self.outdated = outdated
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
            self.session,
            page=index,
            range=self.range,
            start=self.start,
            end=self.end,
            outdated=self.outdated,
            tags=self.tags
        )

    def range_to_dates(self, range, start=None, end=None):
        """ Returns the start and end date for the given range relative to now.
        Defaults to the given start and end date.

        Valid ranges are:
            - today
            - tomorrow
            - weekend (next or current Friday to Sunday)
            - week (current Monday to Sunday)
            - month (current)

        """
        if range not in self.date_ranges:
            return start, end

        today = date.today()
        weekday = today.weekday()

        if range == 'today':
            return today, today
        if range == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            return tomorrow, tomorrow
        if range == 'weekend':
            return (
                today + timedelta(days=4 - weekday),
                today + timedelta(days=6 - weekday)
            )
        if range == 'week':
            return (
                today - timedelta(days=weekday),
                today + timedelta(days=6 - weekday)
            )
        if range == 'month':
            start = today.replace(day=1)
            return start, start + relativedelta(months=1, days=-1)
        pass

    def for_filter(self, **kwargs):
        """ Returns a new instance of the collection with the given filters
        and copies the current filters if not specified.

        If a valid range is provided, start and end dates are ignored. If the
        range is invalid, it is ignored.

        Adds or removes a single tag if given.
        """

        tags = kwargs.get('tags', list(self.tags))
        if 'tag' in kwargs:
            tag = kwargs.get('tag')
            if tag in tags:
                tags.remove(tag)
            elif tag is not None:
                tags.append(tag)

        range = kwargs.get('range', self.range)
        start = kwargs.get('start', self.start)
        end = kwargs.get('end', self.end)
        if 'range' in kwargs and kwargs.get('range') in self.date_ranges:
            range = kwargs.get('range')
            start = None
            end = None
        elif 'start' in kwargs or 'end' in kwargs:
            range = None

        return self.__class__(
            self.session,
            page=0,
            range=range,
            start=start,
            end=end,
            outdated=kwargs.get('outdated', self.outdated),
            tags=tags
        )

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

    def query(self):
        """ Queries occurrences with the set parameters.

        Finds all occurrences with any of the set tags and within the set
        start and end date. Start and end date are assumed to be dates only and
        therefore without a timezone - we search for the given date in the
        timezone of the occurrence!.

        """

        query = self.session.query(Occurrence)

        if self.start is not None or self.outdated is False:
            if self.start is None:
                start = date.today()
            else:
                start = self.start
                if self.outdated is False:
                    start = max(self.start, date.today())
            start = as_datetime(start)

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
            for vevent in event.get_ical_vevents(request.link(event)):
                vcalendar.add_component(vevent)

        return vcalendar.to_ical()
