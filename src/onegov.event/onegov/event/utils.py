from csv import DictReader, DictWriter
from dateutil.parser import parse
from onegov.event.models import Event
from sqlalchemy import distinct


def get_json_keys(session, column):
    """ Returns all keys of a column.

    This could be more efficient with json_object_keys :(.
    """

    result = set()
    for item in session.query(distinct(column)):
        for subitem in item:
            result |= set(subitem.keys())
    return sorted(result)


def export_csv(collection, csvfile):
    """ Exports the given collection to a CSV file with the given name. """

    session = collection.session
    meta_keys = get_json_keys(session, Event.meta)
    content_keys = get_json_keys(session, Event.content)

    headers = [
        'title', 'state', 'start', 'end', 'timezone', 'recurrence', 'tags',
        'location'
    ]
    headers.extend(['meta_{}'.format(i) for i in meta_keys])
    headers.extend(['content_{}'.format(i) for i in content_keys])

    writer = DictWriter(csvfile, fieldnames=headers)
    writer.writeheader()

    for event in collection.query():
        data = {
            'title': event.title,
            'start': event.localized_start.replace(tzinfo=None).isoformat(),
            'end': event.localized_end.replace(tzinfo=None).isoformat(),
            'timezone': event.timezone,
            'tags': ','.join(event.tags),
            'location': event.location,
            'recurrence': event.recurrence,
            'state': event.state,
        }
        for key in meta_keys:
            if key in event.meta:
                data['meta_{}'.format(key)] = event.meta[key]
        for key in content_keys:
            if key in event.content:
                data['content_{}'.format(key)] = event.content[key]
        writer.writerow(data)

    return collection.query().count()


def import_csv(collection, csvfile):
    """ Imports the events from the given CSV file to the given collection. """

    headers = (
        'title', 'state', 'start', 'end', 'timezone', 'recurrence', 'tags',
        'location'
    )

    reader = DictReader(csvfile)

    assert all([
        field in headers or field.startswith('meta_') or
        field.startswith('content_') for field in reader.fieldnames
    ])

    count = 0
    for event in reader:
        count += 1
        meta = {}
        content = {}
        for key in event.keys():
            if key.startswith('meta_') and event[key]:
                meta[key.replace('meta_', '')] = event[key]
            if key.startswith('content_') and event[key]:
                content[key.replace('content_', '')] = event[key]

        added = collection.add(
            title=event.get('title'),
            start=parse(event.get('start')),
            end=parse(event.get('end')),
            timezone=event.get('timezone'),
            location=event.get('location', None),
            recurrence=event.get('recurrence', None),
            tags=[tag for tag in event.get('tags', '').split(',') if tag],
            meta=meta,
            content=content
        )

        state = event.get('state', 'published')
        if state in ('submitted', 'published', 'withdrawn'):
            added.submit()
        if state in ('published', 'withdrawn'):
            added.publish()
        if state in ('withdrawn'):
            added.withdraw()

    return count
