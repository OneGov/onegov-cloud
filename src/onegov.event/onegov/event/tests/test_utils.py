import transaction

from datetime import datetime
from io import StringIO
from onegov.event import EventCollection, Event
from onegov.event.utils import export_csv, import_csv


def test_export_import(session):

    collection = EventCollection(session)

    events = []
    for year in range(2008, 2011):
        for month in range(1, 13):
            tags = ['month-{0}'.format(month)]
            recurrence = 'RRULE:FREQ=DAILY;INTERVAL=1;COUNT=4'
            location = 'location'
            meta = {'1': '3', '2': '2'}
            content = {'a': 'x', 'b': 'z', 'description': 'description'}

            if month == 1:
                content = None
                meta = {'1': '1'}

            if month == 2:
                recurrence = ''
                content = {'a': 'y'}

            if month == 3:
                tags = []
                content = {'d': 'n'}

            if month == 4:
                recurrence = None
                location = ''

            if month == 5:
                meta = {}
                location = None

            if month == 6:
                meta = {'4': '7'}
                content = {}

            if month == 7:
                meta = None

            event = collection.add(
                title='Event {0}-{1}'.format(year, month),
                start=datetime(year, month, 18, 14, 00),
                end=datetime(year, month, 18, 16, 00),
                timezone='US/Eastern',
                tags=tags,
                recurrence=recurrence,
                location=location,
                meta=meta,
                content=content
            )
            event.submit()
            if year > 2008:
                event.publish()
            if year > 2009:
                event.withdraw()

            events.append({
                'state': event.state,
                'title': event.title,
                'localized_start': event.localized_start,
                'localized_end': event.localized_end,
                'timezone': event.timezone,
                'recurrence': event.recurrence or '',
                'tags': event.tags,
                'location': event.location or '',
                'description': event.description,
                'occurrence_dates': event.occurrence_dates(),
                'meta': event.meta,
                'content': event.content,
            })

    transaction.commit()

    output = StringIO()
    assert export_csv(collection, output) == 36
    output.seek(0)

    for event in collection.query():
        collection.delete(event)
    assert collection.query().count() == 0

    import_csv(collection, output)
    assert collection.query().count() == 36

    events = sorted(events, key=lambda x: x['localized_start'])
    for index, event in enumerate(collection.query().order_by(Event.start)):
        assert events[index]['state'] == event.state
        assert events[index]['title'] == event.title
        assert events[index]['localized_start'] == event.localized_start
        assert events[index]['localized_end'] == event.localized_end
        assert events[index]['timezone'] == event.timezone
        assert events[index]['recurrence'] == event.recurrence or ''
        assert events[index]['tags'] == event.tags
        assert events[index]['location'] == event.location or ''
        assert events[index]['description'] == event.description
        assert events[index]['occurrence_dates'] == event.occurrence_dates()
        assert events[index]['meta'] == event.meta
        assert events[index]['content'] == event.content
