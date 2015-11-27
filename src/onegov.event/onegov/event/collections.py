from cached_property import cached_property
from datetime import date, datetime, timedelta
from onegov.core.collection import Pagination
from onegov.core.utils import normalize_for_url, increment_name
from onegov.event.models import Event, Occurrence
from sedate import as_datetime, replace_timezone, standardize_date
from sqlalchemy import and_, distinct, or_
from sqlalchemy.dialects.postgresql import array


class EventCollectionPagination(Pagination):

    def __init__(self, session, page=0, state='submitted'):
        self.session = session
        self.page = page
        self.state = state

    def __eq__(self, other):
        return self.state == other.state and self.page == other.page

    def subset(self):
        query = self.query()
        query = query.order_by(Event.start)
        query = query.filter(Event.state == self.state)

        return query

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index, self.state)

    def for_state(self, state):
        """ Returns a new instance of the collection with the given state. """

        return self.__class__(self.session, 0, state)


class EventCollection(EventCollectionPagination):
    """ Manage a list of events. """

    def query(self):
        return self.session.query(Event)

    def _get_unique_name(self, name):
        """ Create a unique, URL-friendly name. """

        # it's possible for `normalize_for_url` to return an empty string...
        name = normalize_for_url(name) or "event"

        session = self.session
        while session.query(Event.name).filter(Event.name == name).first():
            name = increment_name(name)

        return name

    def add(self, title, start, end, timezone, autoclean=True, **optional):
        """ Add a new event.

        A unique, URL-friendly name is created automatically for this event
        using the title and optionally numbers for duplicate names.

        Every time a new event is added, old, stale events are deleted unless
        disabled with the ``autoclean`` option.

        Returns the created event or None if already automatically deleted.
        """
        event = Event(
            state='initiated',
            title=title,
            start=replace_timezone(start, timezone),
            end=replace_timezone(end, timezone),
            timezone=timezone,
            name=self._get_unique_name(title),
            **optional
        )

        self.session.add(event)
        self.session.flush()

        if autoclean:
            self.remove_stale_events()

        return event

    def delete(self, event):
        """ Delete an event. """

        self.session.delete(event)
        self.session.flush()

    def remove_stale_events(self, max_stale=None):
        """ Remove events which have never been submitted and are created more
        than five days ago.

        """

        if max_stale is None:
            max_stale = datetime.utcnow() - timedelta(days=5)
            max_stale = standardize_date(max_stale, 'UTC')

        events = self.session.query(Event).filter(
            Event.state == 'initiated',
            and_(
                or_(Event.created < max_stale, Event.created.is_(None)),
                or_(Event.modified < max_stale, Event.modified.is_(None))
            )
        )
        for event in events:
            self.session.delete(event)

        self.session.flush()

    def by_name(self, name):
        """ Returns an event by its URL-friendly name. """

        query = self.session.query(Event).filter(Event.name == name)
        return query.first()

    def by_id(self, id):
        """ Return an event by its id. """

        query = self.session.query(Event).filter(Event.id == id)
        return query.first()


class OccurrenceCollectionPagination(Pagination):

    def __init__(self, session, page=0, start=None, end=None, tags=None):
        self.session = session
        self.page = page
        self.start = start
        self.end = end
        self.tags = tags if tags else []

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        return self.query(start=self.start, end=self.end, tags=self.tags)

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


class OccurrenceCollection(OccurrenceCollectionPagination):
    """ Manages a list of occurrences.

    Occurrences are read only (no ``add`` method here), they are generated
    automatically when adding a new event.

    Occurrences can be filtered by start and end dates as well as tags.

    By default, only current occurrences are returned.
    """

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
        tags = []
        for result in self.session.query(distinct(Occurrence._tags.keys())):
            tags.extend(result[0])

        return sorted(set(tags))

    def query(self, start=None, end=None, tags=None, outdated=False):
        """ Queries occurrences with the given parameters.

        Finds all occurrences with any of the given tags and within the given
        start and end date. Start and end date are assumed to be dates only and
        therefore without a timezone - we search for the given date in the
        timezone of the occurrence!.

        If no start date is given and ``outdated`` is not set, only current
        occurrences are returned.
        """

        query = self.session.query(Occurrence)

        if start is not None:
            assert type(start) is date
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

        if end is not None:
            assert type(end) is date
            end = as_datetime(end)
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

        if tags:
            query = query.filter(Occurrence._tags.has_any(array(tags)))

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
