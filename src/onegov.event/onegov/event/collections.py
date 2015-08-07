from onegov.event.models import Event, Occurrence
from sedate import replace_timezone
from sqlalchemy import or_


class EventCollection(object):

    def __init__(self, session):
        self.session = session

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

        return event

    def delete(self, event):
        self.session.delete(event)
        self.session.flush()


class OccurrenceCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self, start=None, end=None, tags=None):
        query = self.session.query(Occurrence)

        if start is not None:
            query = query.filter(Occurrence.start >= start)

        if end is not None:
            query = query.filter(Occurrence.end <= end)

        if tags is not None:
            query = query.filter(or_(*(
                Occurrence.tags.like('%{0}%'.format(tag)) for tag in tags
            )))

        return query
