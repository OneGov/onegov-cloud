from onegov.event.models import Event, Occurrence
from sqlalchemy import or_


class EventCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Event)

    def add(self, start, end, title, **optional):
        event = Event(
            state='initiated', start=start, end=end, title=title, **optional
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
