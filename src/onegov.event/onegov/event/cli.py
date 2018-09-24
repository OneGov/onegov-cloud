import click

from csv import reader as csvreader
from dateutil.parser import parse
from hashlib import sha1
from lxml import etree
from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.event import log
from onegov.event.collections import EventCollection
from onegov.event.models import Event
from onegov.event.models import Occurrence
from onegov.event.utils import GuidleExportData
from onegov.gis import Coordinates
from operator import add
from requests import get
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import array

cli = command_group()


@cli.command('clear')
@pass_group_context
def clear(group_context):
    """ Deletes all events.

        onegov-event --select '/veranstaltungen/zug' clear

    """

    def _clear(request, app):
        if not click.confirm("Do you really want to remove all events?"):
            abort("Deletion process aborted")

        session = app.session()
        for event in session.query(Event):
            session.delete(event)
        for occurrence in session.query(Occurrence):
            session.delete(occurrence)

    return _clear


@cli.command('import-json')
@pass_group_context
@click.argument('url')
@click.option('--tagmap', type=click.File())
def import_json(group_context, url, tagmap):
    """ Fetches the events from a seantis.dir.events instance.

    This command is intended for migration and to be removed in the future.

    Example:

        onegov-event --select '/veranstaltungen/zug' import-json \
        'https://veranstaltungen.zug.ch/veranstaltungen/?type=json&compact'

    """
    if tagmap:
        tagmap = {row[0]: row[1] for row in csvreader(tagmap)}

    def _import_json(request, app):
        unknown_tags = set()

        response = get(url)
        response.raise_for_status()
        response = response.json()

        session = app.session()
        events = EventCollection(session)

        for item in response:
            title = item['title']

            start = parse(item['start'])
            end = parse(item['end'])
            timezone = item['timezone']
            recurrence = item['recurrence']

            organizer = ', '.join((line for line in (
                item['organizer'] or '',
                item['contact_name'] or '',
                item['contact_email'] or '',
                item['contact_phone'] or ''
            ) if line))

            location = ', '.join((line for line in (
                item['locality'] or '',
                ' '.join((
                    item['street'] or '',
                    item['housenumber'] or ''
                )).strip(),
                ' '.join((
                    item['zipcode'] or '',
                    item['town'] or '',
                )).strip(),
            ) if line))

            description = '\r\n\r\n'.join((line for line in (
                item['short_description'] or '',
                item['long_description'] or '',
                item['event_url'] or '',
                item['location_url'] or '',
                item['prices'],
                item['registration']
            ) if line))

            tags = item['cat1']
            if tagmap and tags:
                unknown_tags |= set(tags) - tagmap.keys()
                tags = {tagmap[tag] for tag in tags if tag in tagmap}
            # todo: handle item['cat2']

            coordinates = None
            if item['latitude'] and item['longitude']:
                coordinates = Coordinates(
                    lat=item['latitude'],
                    lon=item['longitude']
                )

            event = Event(
                state='initiated',
                name=events._get_unique_name(title),
                title=title,
                start=start,
                end=end,
                recurrence=recurrence,
                timezone=timezone,
                description=description,
                organizer=organizer,
                location=location,
                coordinates=coordinates,
                tags=tags or [],
                meta={'submitter_email': item['submitter_email']},
            )
            # todo: handle item['attachments']
            # todo: handle item['images']
            session.add(event)
            event.submit()
            event.publish()

        if unknown_tags:
            unknown_tags = ', '.join([f'"{tag}"' for tag in unknown_tags])
            click.secho(f"Tags not in tagmap: {unknown_tags}!", fg='yellow')

        click.secho(f"Imported {len(response)} events", fg='green')

    return _import_json


@cli.command('import-ical')
@pass_group_context
@click.argument('ical', type=click.File())
def import_ical(group_context, ical):
    """ Imports events from an iCalendar file.

    Example:

        onegov-event --select '/veranstaltungen/zug' import-ical import.ics

    """

    def _import_ical(request, app):
        collection = EventCollection(app.session())
        added, updated, purged = collection.from_ical(ical.read())
        click.secho(
            f"Events successfully imported "
            f"({added} added, {updated} updated, {purged} deleted)",
            fg='green')

    return _import_ical


@cli.command('import-guidle')
@pass_group_context
@click.argument('url')
@click.option('--tagmap', type=click.File())
def import_guidle(group_context, url, tagmap):
    """ Fetches the events from guidle.

    Example:

        onegov-event --select '/veranstaltungen/zug' import-guidle \
        'http://www.guidle.com/xxxx/'

    """
    if tagmap:
        tagmap = {row[0]: row[1] for row in csvreader(tagmap)}

    def _import_guidle(request, app):
        try:
            response = get(url)
            response.raise_for_status()

            unknown_tags = set()
            prefix = 'guidle-{}'.format(sha1(url.encode()).hexdigest()[:10])

            events = []
            root = etree.fromstring(response.text.encode('utf-8'))
            for offer in GuidleExportData(root).offers():
                tags, unknown = offer.tags(tagmap)
                unknown_tags |= unknown
                for index, schedule in enumerate(offer.schedules()):
                    events.append(
                        Event(
                            state='initiated',
                            title=offer.title,
                            start=schedule.start,
                            end=schedule.end,
                            recurrence=schedule.recurrence,
                            timezone=schedule.timezone,
                            description=offer.description,
                            organizer=offer.organizer,
                            location=offer.location,
                            coordinates=offer.coordinates,
                            tags=tags,
                            meta={'source': f'{prefix}-{offer.uid}.{index}'},
                        )
                    )
                # todo: handle attachements
                # todo: handle images

            collection = EventCollection(app.session())
            added, updated, purged = collection.from_import(events, prefix)

            if unknown_tags:
                unknown_tags = ', '.join([f'"{tag}"' for tag in unknown_tags])
                click.secho(
                    f"Tags not in tagmap: {unknown_tags}!", fg='yellow'
                )

            click.secho(
                f"Events successfully imported from '{url}' "
                f"({added} added, {updated} updated, {purged} deleted)",
                fg='green'
            )
        except Exception as e:
            log.error("Error importing events", exc_info=True)
            raise(e)

    return _import_guidle


@cli.command()
@pass_group_context
@click.option('--source', multiple=True)
@click.option('--tag', multiple=True)
@click.option('--location', multiple=True)
def fetch(group_context, source, tag, location):
    """ Fetches events from other instances.

    Only fetches events from the same namespace which have not been imported
    themselves.

    Example

        onegov-event --select '/veranstaltungen/zug' fetch \
            --source menzingen --source steinhausen
            --tag Sport --tag Konzert

    """

    def vector_add(a, b):
        return list(map(add, a, b))

    if not len(source):
        abort("Provide at least one source")

    def _fetch(request, app):
        try:
            local_session = app.session()
            local_events = EventCollection(local_session)
            assert local_session.info['schema'] == app.schema

            result = [0, 0, 0]
            for key in source:
                schema = '{}-{}'.format(app.namespace, key)
                assert schema in app.session_manager.list_schemas()
                app.session_manager.set_current_schema(schema)
                remote_session = app.session_manager.session()
                assert remote_session.info['schema'] == schema

                query = remote_session.query(Event)
                query = query.filter(Event.meta['source'].is_(None))
                if tag:
                    query = query.filter(Event._tags.has_any(array(tag)))
                if location:
                    query = query.filter(
                        or_(*[
                            Event.location.ilike(f'%{term}%')
                            for term in location
                        ])
                    )
                remote_events = [
                    Event(
                        state='initiated',
                        title=event.title,
                        start=event.start,
                        end=event.end,
                        timezone=event.timezone,
                        recurrence=event.recurrence,
                        content=event.content,
                        location=event.location,
                        tags=event.tags,
                        meta={'source': f'fetch-{key}-{event.name}'},
                        coordinates=event.coordinates,
                    ) for event in query
                ]
                result = vector_add(
                    result,
                    local_events.from_import(remote_events, f'fetch-{key}')
                )
                # todo: attachments

            click.secho(
                f"Events successfully fetched "
                f"({result[0]} added, {result[1]} updated, "
                f"{result[2]} deleted)",
                fg='green'
            )

        except Exception as e:
            log.error("Error fetching events", exc_info=True)
            raise(e)

    return _fetch
