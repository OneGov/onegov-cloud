from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta, datetime


import sqlalchemy
from dateutil.relativedelta import relativedelta
from enum import Enum
from functools import cached_property
from icalendar import Calendar as vCalendar
from lxml import etree, objectify
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sqlalchemy import distinct, func
from sqlalchemy import or_, and_
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import undefer

from onegov.core.collection import Pagination
from onegov.core.utils import toggle
from onegov.event.models import Event
from onegov.event.models import Occurrence
from onegov.form import as_internal_id


from typing import assert_never
from typing import Any
from typing import Literal
from typing import TypeVar
from typing import Self
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Mapping
    from collections.abc import Sequence
    from onegov.core.request import CoreRequest
    from onegov.form.parser.core import ParsedField
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Protocol
    from typing import TypeAlias

    class OccurenceSearchWidget(Protocol):
        @property
        def name(self) -> str: ...
        @property
        def search_query(self) -> Query[Occurrence]: ...

        def adapt(
            self,
            query: Query[Occurrence]
        ) -> Query[Occurrence]: ...

    T = TypeVar('T')
    MissingType: TypeAlias = 'Literal[_Sentinel.MISSING]'

DateRange = Literal[
    'today',
    'tomorrow',
    'weekend',
    'week',
    'month',
    'past'
]


class _Sentinel(Enum):
    MISSING = object()


MISSING = _Sentinel.MISSING


class OccurrenceCollection(Pagination[Occurrence]):
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

    date_ranges: tuple[DateRange, ...] = (
        'today',
        'tomorrow',
        'weekend',
        'week',
        'month',
        'past'
    )

    def __init__(
        self,
        session: Session,
        page: int = 0,
        range: DateRange | None = None,
        start: date | None = None,
        end: date | None = None,
        outdated: bool = False,
        tags: Sequence[str] | None = None,
        filter_keywords: Mapping[str, list[str] | str] | None = None,
        locations: Sequence[str] | None = None,
        only_public: bool = False,
        search_widget: OccurenceSearchWidget | None = None,
        event_filter_configuration: dict[str, Any] | None = None,
        event_filter_fields: Sequence[ParsedField] | None = None,
    ) -> None:

        super().__init__(page=page)
        self.session = session
        self.range = range if range in self.date_ranges else None
        self.start, self.end = self.range_to_dates(range, start, end)
        self.outdated = outdated
        self.tags = tags if tags else []
        self.filter_keywords = filter_keywords or {}
        self.locations = locations if locations else []
        self.only_public = only_public
        self.search_widget = search_widget
        self.event_filter_configuration = event_filter_configuration or {}
        self.event_filter_fields = event_filter_fields or ()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page

    def subset(self) -> Query[Occurrence]:
        return self.query()

    @property
    def search(self) -> str | None:
        return self.search_widget.name if self.search_widget else None

    @property
    def search_query(self) -> Query[Occurrence] | None:
        return self.search_widget.search_query if self.search_widget else None

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            range=self.range,
            start=self.start,
            end=self.end,
            outdated=self.outdated,
            tags=self.tags,
            filter_keywords=self.filter_keywords,
            locations=self.locations,
            only_public=self.only_public,
            search_widget=self.search_widget,
            event_filter_configuration=self.event_filter_configuration,
            event_filter_fields=self.event_filter_fields,
        )

    def range_to_dates(
        self,
        range: DateRange | None,
        start: date | None = None,
        end: date | None = None
    ) -> tuple[date | None, date | None]:
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

        assert_never(range)

    def for_keywords(
        self,
        singular: bool = False,
        **keywords: list[str]
    ) -> Self:

        return self.__class__(
            self.session,
            page=0,
            range=self.range,
            start=self.start,
            end=self.end,
            outdated=self.outdated,
            tags=self.tags,
            filter_keywords=keywords,
            locations=self.locations,
            only_public=self.only_public,
            search_widget=self.search_widget,
            event_filter_configuration=self.event_filter_configuration,
            event_filter_fields=self.event_filter_fields,
        )

    def for_toggled_keyword_value(
        self,
        keyword: str,
        value: str,
        singular: bool = False,
    ) -> Self:

        parameters = dict(self.filter_keywords)

        collection = set(parameters.get(keyword, []))

        if singular:
            collection = set() if value in collection else {value}
        else:
            collection = toggle(collection, value)

        if collection:
            parameters[keyword] = sorted(collection)
        elif keyword in parameters:
            del parameters[keyword]

        return self.__class__(
            self.session,
            page=0,
            range=self.range,
            start=self.start,
            end=self.end,
            outdated=self.outdated,
            tags=self.tags,
            filter_keywords=parameters,
            locations=self.locations,
            only_public=self.only_public,
            search_widget=self.search_widget,
            event_filter_configuration=self.event_filter_configuration,
            event_filter_fields=self.event_filter_fields,
        )

    def for_filter(
        self,
        *,
        range: DateRange | None = None,
        start: date | MissingType | None = MISSING,
        end: date | MissingType | None = MISSING,
        outdated: bool | None = None,
        tags: Sequence[str] | None = None,
        tag: str | None = None,
        locations: Sequence[str] | None = None,
        location: str | None = None,
    ) -> Self:
        """ Returns a new instance of the collection with the given filters
        and copies the current filters if not specified.

        If a valid range is provided, start and end dates are ignored. If the
        range is invalid, it is ignored.

        Adds or removes a single tag/location if given.
        """
        if range in self.date_ranges:
            start = None
            end = None
        elif start is not MISSING or end is not MISSING:
            range = None
        elif range is None:
            range = self.range

        if start is MISSING:
            start = self.start

        if end is MISSING:
            end = self.end

        tags = list(self.tags if tags is None else tags)
        if tag is not None:
            if tag in tags:
                tags.remove(tag)
            else:
                tags.append(tag)

        locations = list(self.locations if locations is None else locations)
        if location is not None:
            if location in locations:
                locations.remove(location)
            else:
                locations.append(location)

        return self.__class__(
            self.session,
            page=0,
            range=range,
            start=start,
            end=end,
            outdated=self.outdated if outdated is None else outdated,
            tags=tags,
            filter_keywords=self.filter_keywords,
            locations=locations,
            only_public=self.only_public,
            search_widget=self.search_widget,
            event_filter_configuration=self.event_filter_configuration,
            event_filter_fields=self.event_filter_fields,
        )

    def without_keywords_and_tags(self) -> Self:
        return self.__class__(
            self.session,
            page=self.page,
            range=self.range,
            start=self.start,
            end=self.end,
            outdated=self.outdated,
            tags=None,
            filter_keywords=None,
            locations=self.locations,
            only_public=self.only_public,
            search_widget=self.search_widget,
            event_filter_configuration=self.event_filter_configuration,
            event_filter_fields=self.event_filter_fields,
        )

    @cached_property
    def used_timezones(self) -> list[str]:
        """ Returns a list of all the timezones used by the occurrences. """

        return [
            tz for tz, in self.session.query(distinct(Occurrence.timezone))
        ]

    @cached_property
    def tag_counts(self) -> dict[str, int]:
        """
        Returns a dict with all existing tags as keys and the number of
        existence as value.

        """
        counts: dict[str, int] = defaultdict(int)

        base = self.session.query(Occurrence._tags.keys())  # type:ignore
        base = base.filter(func.DATE(Occurrence.end) >= date.today())

        for keys, in base:
            for tag in keys:
                counts[tag] += 1

        return counts

    def set_event_filter_configuration(
        self,
        config: dict[str, Any] | None
    ) -> None:

        self.event_filter_configuration = config or {}

    def set_event_filter_fields(
        self,
        fields: Sequence[ParsedField] | None
    ) -> None:

        self.event_filter_fields = fields or ()

    def valid_keywords(
        self,
        parameters: Mapping[str, T]
    ) -> dict[str, T]:

        valid_keywords = {
            as_internal_id(kw)
            for kw in self.event_filter_configuration.get('keywords') or ()
        }
        return {
            k_id: v
            for k, v in parameters.items()
            if (k_id := as_internal_id(k)) in valid_keywords
        }

    def available_filters(
        self,
        sort_choices: bool = False,
        sortfunc: Callable[[str], SupportsRichComparison] | None = None
    ) -> Iterable[tuple[str, str, list[str]]]:
        """
        Retrieve the filters with their choices. Return by default in the
        order of how they are defined in the config structure.
        To filter alphabetically, set sort_choices=True.

        :return tuple containing tuples with keyword, label and list of values
        :rtype tuple(tuples(keyword, title, values as list)

        """
        if not self.event_filter_configuration or not self.event_filter_fields:
            return ()

        keywords = tuple(
            as_internal_id(k) for k in
            self.event_filter_configuration.get('keywords', set)
        )

        fields = {
            f.id: f for f in self.event_filter_fields
            if f.id in keywords and (
                f.type == 'radio'
                or f.type == 'checkbox'
            )
        }

        def maybe_sorted(values: Iterable[str]) -> list[str]:
            if not sort_choices:
                return list(values)
            return sorted(values, key=sortfunc)

        if not fields:
            return set()

        return (
            (k, f.label, maybe_sorted(c.label for c in f.choices))
            for k in keywords if hasattr((f := fields[k]), 'choices')
        )

    @cached_property
    def used_tags(self) -> set[str]:
        """ Returns a list of all the tags used by all future occurrences.

        """

        query = self.session.query(
            sqlalchemy.func.skeys(Occurrence._tags),
        ).filter(func.DATE(Occurrence.end) >= date.today())
        return {key[0] for key in query.distinct()}

    def query(self) -> Query[Occurrence]:
        """ Queries occurrences with the set parameters.

        Finds occurrences which:
        * are between start and end date
        * have any of the tags
        * have any of the locations (exact word)

        Start and end date are assumed to be dates only and therefore without
        a timezone - we search for the given date in the timezone of the
        occurrence.

        In case of a search widget request the query will filter for events
        containing the text search term in e.g. title

        """

        query = (
            self.session.query(Occurrence).join(Event)
            .options(contains_eager(Occurrence.event).joinedload(Event.image))
        )

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
            for tz in self.used_timezones:
                localized_start = replace_timezone(start, tz)
                localized_start = standardize_date(localized_start, tz)
                expressions.append(
                    and_(
                        Occurrence.timezone == tz,
                        Occurrence.start >= localized_start
                    )
                )
            if expressions:
                query = query.filter(or_(*expressions))

        if self.end is not None:
            end = as_datetime(self.end)
            end = end + timedelta(days=1)

            expressions = []
            for tz in self.used_timezones:
                localized_end = replace_timezone(end, tz)
                localized_end = standardize_date(localized_end, tz)
                expressions.append(
                    and_(
                        Occurrence.timezone == tz,
                        Occurrence.end < localized_end
                    )
                )

            query = query.filter(or_(*expressions))

        if self.tags:
            query = query.filter(
                Occurrence._tags.has_any(array(self.tags))  # type:ignore
            )

        if self.filter_keywords:
            keywords = self.valid_keywords(self.filter_keywords)

            values = [val for sublist in keywords.values() for val in sublist]
            values.sort()

            values = [
                Event.filter_keywords[keyword].has_any(  # type:ignore[index]
                    array(values)  # type:ignore[call-overload]
                )
                for keyword in keywords.keys()
            ]

            if values:
                query = query.filter(and_(*values))

        if self.locations:

            def escape(qstring: str) -> str:
                purge = "\\(),\"'."
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

        if self.search_widget:
            query = self.search_widget.adapt(query)

        return query

    def by_name(self, name: str) -> Occurrence | None:
        """ Returns an occurrence by its URL-friendly name.

        The URL-friendly name is automatically constructed as follows:

        ``unique name of the event``-``date of the occurrence``

        e.g.

        ``squirrel-park-visit-6-2015-06-20``

        """

        query = self.session.query(Occurrence).filter(Occurrence.name == name)
        return query.first()

    def by_id(self, id: str) -> Occurrence | None:
        """ Returns an occurrence by its id. """

        query = self.session.query(Occurrence).filter(Occurrence.id == id)
        return query.first()

    def as_ical(self, request: CoreRequest) -> bytes:
        """ Returns the the events of the given occurrences as iCalendar
        string.

        """

        vcalendar = vCalendar()
        vcalendar.add('prodid', '-//OneGov//onegov.event//')
        vcalendar.add('version', '2.0')

        query = self.query().with_entities(Occurrence.event_id)
        event_ids = {event_id for event_id, in query}

        query = self.session.query(Event).filter(Event.id.in_(event_ids))
        query = query.options(undefer(Event.content))
        for event in query:
            for vevent in event.get_ical_vevents(request.link(event)):
                vcalendar.add_component(vevent)

        return vcalendar.to_ical()

    def as_xml(self, future_events_only: bool = True) -> bytes:
        """
        Returns all published occurrences as xml.

        The xml format was Winterthur's wish (no specs behind). Their mobile
        app will consume the events from.

        Format::

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

        query = self.session.query(Occurrence).options(
            # load relevant event eagerly
            joinedload(Occurrence.event)
        )
        for occ in query:
            e = occ.event

            if e.state != 'published':
                continue
            if future_events_only and datetime.fromisoformat(str(
                    occ.end)).date() < datetime.today().date():
                continue

            event = objectify.Element('event')
            event.id = e.id
            event.title = e.title
            txs = Tags(e.tags)
            event.append(txs)  # type:ignore[arg-type]
            event.description = e.description
            event.start = e.localized_start
            event.end = e.localized_end
            event.location = e.location
            event.price = e.price
            event.organizer = e.organizer
            event.event_url = e.external_event_url
            event.organizer_email = e.organizer_email
            event.organizer_phone = e.organizer_phone
            event.modified = e.last_change
            root.append(event)

        # remove lxml annotations
        objectify.deannotate(root, pytype=True, xsi=True, xsi_nil=True)
        etree.cleanup_namespaces(root)

        return etree.tostring(root, encoding='utf-8', xml_declaration=True,
                              pretty_print=True)


class Tags(etree.ElementBase):
    """
    Custom class as 'tag' is a member of class Element and cannot be
    used as tag name.
    """

    def __init__(self, tags: Sequence[str] = ()) -> None:  # type:ignore
        super().__init__()
        self.tag = 'tags'

        for t in tags:
            tag = etree.Element('tag')
            tag.text = t
            self.append(tag)  # type:ignore[arg-type]
