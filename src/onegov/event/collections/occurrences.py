import datetime
from collections import defaultdict

import sqlalchemy

from functools import cached_property
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from icalendar import Calendar as vCalendar
from lxml import objectify, etree
from onegov.core.collection import Pagination
from onegov.event.models import Event
from onegov.event.models import Occurrence
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sqlalchemy import and_
from sqlalchemy import distinct
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.orm import contains_eager


class OccurrenceCollection(Pagination):
    """ Manages a list of occurrences.

    Occurrences are read only (no ``add`` method here), they are generated
    automatically when adding a new event.

    Occurrences can be filtered by relative date ranges (``today``,
    ``tomorrow``, ``weekend``, ``week``, ``month``, ``past``) or by a
    given start date and/or end date. The range filter is dominant and
    overwrites the start and end dates if provided.

    By default, only current occurrences are used.

    Occurrences can be additionally filtered by tags and locations.

    """

    date_ranges = ('today', 'tomorrow', 'weekend', 'week', 'month', 'past')

    def __init__(
        self,
        session,
        page=0,
        range=None,
        start=None,
        end=None,
        outdated=False,
        tags=None,
        locations=None,
        only_public=False,
    ):
        self.session = session
        self.page = page
        self.range = range if range in self.date_ranges else None
        self.start, self.end = self.range_to_dates(range, start, end)
        self.outdated = outdated
        self.tags = tags if tags else []
        self.locations = locations if locations else []
        self.only_public = only_public

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
            tags=self.tags,
            locations=self.locations,
            only_public=self.only_public,
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
            - past (events in the past)

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
        if range == 'past':
            millennium = date(2000, 1, 1)
            yesterday = today - timedelta(days=1)
            return millennium, yesterday
        pass

    def for_filter(self, **kwargs):
        """ Returns a new instance of the collection with the given filters
        and copies the current filters if not specified.

        If a valid range is provided, start and end dates are ignored. If the
        range is invalid, it is ignored.

        Adds or removes a single tag/location if given.
        """

        range = kwargs.get('range', self.range)
        start = kwargs.get('start', self.start)
        end = kwargs.get('end', self.end)
        if 'range' in kwargs and kwargs.get('range') in self.date_ranges:
            range = kwargs.get('range')
            start = None
            end = None
        elif 'start' in kwargs or 'end' in kwargs:
            range = None

        tags = kwargs.get('tags', list(self.tags))
        if 'tag' in kwargs:
            tag = kwargs.get('tag')
            if tag in tags:
                tags.remove(tag)
            elif tag is not None:
                tags.append(tag)

        locations = kwargs.get('locations', list(self.locations))
        if 'location' in kwargs:
            location = kwargs.get('location')
            if location in locations:
                locations.remove(location)
            elif location is not None:
                locations.append(location)

        return self.__class__(
            self.session,
            page=0,
            range=range,
            start=start,
            end=end,
            outdated=kwargs.get('outdated', self.outdated),
            tags=tags,
            locations=locations,
            only_public=self.only_public,
        )

    @cached_property
    def used_timezones(self):
        """ Returns a list of all the timezones used by the occurrences. """

        return [
            tz[0] for tz in self.session.query(distinct(Occurrence.timezone))
        ]

    @cached_property
    def tag_counts(self) -> defaultdict[str, int]:
        """
        Returns a dict with all existing tags as keys and the number of
        existence as value.

        """
        counts = defaultdict(int)  # type: defaultdict[str, int]

        base = self.session.query(Occurrence._tags.keys())
        base = base.filter(Occurrence.start >= datetime.datetime.now(
            datetime.timezone.utc))

        for keys in base.all():
            for tag in keys[0]:
                counts[tag] += 1

        return counts

    @cached_property
    def used_tags(self):
        """ Returns a list of all the tags used by all future occurrences.

        This could be solve possibly more effienciently with the skey function
        currently not supported by SQLAlchemy (e.g.
        ``select distinct(skeys(tags))``), see
        http://stackoverflow.com/q/12015942/3690178

        """
        base = self.session.query(Occurrence._tags.keys()).with_entities(
            sqlalchemy.func.skeys(Occurrence._tags).label('keys'),
            Occurrence.start)
        base = base.filter(Occurrence.start >= datetime.datetime.now(
            datetime.timezone.utc))

        query = sqlalchemy.select(
            [sqlalchemy.func.array_agg(sqlalchemy.column('keys'))],
            distinct=True
        ).select_from(base.subquery())
        keys = self.session.execute(query).scalar()
        return set(keys) if keys else set()

    def query(self):
        """ Queries occurrences with the set parameters.

        Finds occurrences which:
        * are between start and end date
        * have any of the tags
        * have any of the locations (exact word)

        Start and end date are assumed to be dates only and therefore without
        a timezone - we search for the given date in the timezone of the
        occurrence.

        """

        query = self.session.query(Occurrence).join(Event)\
            .options(contains_eager(Occurrence.event).joinedload(Event.image))

        if self.only_public:
            query = query.filter(or_(
                Event.meta['access'].astext == 'public',
                Event.meta['access'].astext == None
            ))

        if self.start is not None or self.outdated is False:
            if self.start is None:
                start = date.today()
            elif self.range == 'past':
                start = self.start
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
            if expressions:
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

        if self.locations:

            def escape(qstring):
                purge = "\\(),\"\'."
                for s in purge:
                    qstring = qstring.replace(s, '')
                return qstring

            query = query.filter(
                or_(*[
                    Occurrence.location.op('~')(f'\\y{escape(loc)}\\y')
                    for loc in self.locations
                ])
            )

        if self.range == 'past':
            # reverse order for past events: most recent event on top
            query = query.order_by(Occurrence.start.desc(), Occurrence.title)
        else:
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

    def as_xml(self, future_events_only=False):
        """
        Returns all published occurrences as xml.

        The xml format was Winterthur's wish (no specs behind). Their mobile
        app will consume the events from xml

        Format:
        <events>
            <event>
                <id></id>
                <title></title>
                <tags></tags>
                    <tag></tag>
                <description></description>
                <start></start>
                <end></end>
                <location></location>
                <price></price>
                ..
            </event>
            <event>
                ..
            </event>
            ..
        </events>

        :param future_events_only: if set, only future events will be
        returned, all events otherwise
        :rtype: str
        :return: xml string
        """
        xml = '<events></events>'
        root = objectify.fromstring(xml)

        query = self.session.query(Occurrence)
        for occ in query:
            e = self.session.query(Event).\
                filter(Event.id == occ.event_id).first()

            if e.state != 'published':
                continue
            if future_events_only and datetime.fromisoformat(str(
                    occ.end)).date() < datetime.today().date():
                continue

            event = objectify.Element('event')
            event.id = e.id
            event.title = e.title
            txs = tags(e.tags)
            event.append(txs)
            event.description = e.description
            event.start = occ.start
            event.end = occ.end
            event.location = e.location
            event.price = e.price
            event.organizer = e.organizer
            event.event_url = e.external_event_url
            event.organizer_email = e.organizer_email
            event.modified = e.last_change
            root.append(event)

        # remove lxml annotations
        objectify.deannotate(root, pytype=True, xsi=True, xsi_nil=True)
        etree.cleanup_namespaces(root)

        return etree.tostring(root, encoding='utf-8', xml_declaration=True,
                              pretty_print=True)


class tags(etree.ElementBase):
    """
    Custom class as 'tag' is a member of class Element and cannot be
    used as tag name.
    """

    def __init__(self, tags=()):
        super().__init__()
        self.tag = 'tags'

        for t in tags:
            tag = etree.Element('tag')
            tag.text = t
            self.append(tag)
