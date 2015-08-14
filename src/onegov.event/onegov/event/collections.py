from cached_property import cached_property
from datetime import date, datetime, timedelta
from onegov.core.collection import Pagination
from onegov.event.models import Event, Occurrence
from sedate import as_datetime, replace_timezone, standardize_date
from sqlalchemy import and_, distinct, or_


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


class EventCollection(EventCollectionPagination):

    def query(self):
        return self.session.query(Event)

    def add(self, title, start, end, timezone, **optional):
        event = Event(
            state='initiated',
            title=title,
            start=replace_timezone(start, timezone),
            end=replace_timezone(end, timezone),
            timezone=timezone,
            **optional
        )

        self.session.add(event)
        self.session.flush()

        self.remove_old_events()

        return event

    def delete(self, event):
        self.session.delete(event)
        self.session.flush()

    def remove_old_events(self, max_age=None):
        if max_age is None:
            max_age = datetime.utcnow() - timedelta(days=30)
            max_age = standardize_date(max_age, 'UTC')

        events = self.session.query(Event).filter(Event.start < max_age)
        events = list(filter(
            lambda x: max(x.occurrence_dates(limit=False)) < max_age, events
        ))
        for event in events:
            self.session.delete(event)

        self.session.flush()


class OccurrenceCollectionPagination(Pagination):
    """ Implements pagination for displaying event occurrences. """

    def __init__(self, session, page=0, start=None, end=None, tags=None):
        self.session = session
        self.start = start
        self.end = end
        self.tags = tags if tags else []
        self.page = page

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
    """

    @cached_property
    def used_timezones(self):
        """ Returns a list of all the timezones used by the occurrences. """
        return [
            tz[0] for tz in self.session.query(distinct(Occurrence.timezone))
        ]

    @cached_property
    def used_tags(self):
        """ Returns a list of all the tags used by the occurrences. """
        # todo: optimize this with hstore
        tags = []
        for occurrence in self.session.query(Occurrence):
            tags.extend([tag.strip() for tag in occurrence.tags.split(',')])

        return sorted(set(tags))

    def query(self, start=None, end=None, tags=None):
        """ Queries occurrences with the given parameters.

        Finds all occurrences with any of the given tags and within the given
        start and end date. Start and end date are assumed to be dates only and
        therefore without a timezone - we search for the given date in the
        timezone of the occurrence!.
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

        if tags is not None:
            query = query.filter(or_(*(
                Occurrence.tags.like('%{0}%'.format(tag)) for tag in tags
            )))

        query = query.order_by(Occurrence.start)

        return query

    # todo: remove, replace with by name
    def by_id(self, id):
        return self.query().filter(Occurrence.id == id).first()
