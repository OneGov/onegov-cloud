import click
import pycurl

from csv import reader as csvreader
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from hashlib import sha1
from icalendar import Calendar as vCalendar
from io import BytesIO
from lxml import etree
from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.event import log
from onegov.event.collections import EventCollection
from onegov.event.collections.events import EventImportItem
from onegov.event.models import Event
from onegov.event.models import EventFile
from onegov.event.models import Occurrence
from onegov.event.utils import as_rdates
from onegov.event.utils import GuidleExportData
from onegov.file import DepotApp
from onegov.file.utils import as_fileintent
from onegov.gis import Coordinates
from operator import add
from pathlib import Path
from pytz import UTC
from requests import get
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sedate import to_timezone
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import array
from urllib.parse import urlparse


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


def download_image(image_url):
    buffer = BytesIO()

    c = pycurl.Curl()
    c.setopt(c.URL, image_url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)

    try:
        c.perform()

        if c.getinfo(c.RESPONSE_CODE) != 200:
            return None

    finally:
        c.close()

    return buffer


def get_event_dates(url, timezone):
    """ Get the start and end datetime of an event in a seantis.dir.events
    events calendar.

    The start and end datetime in the seantis.dir.events JSON export is
    wrong since they refer to the next occurrence and not the first one. This
    is unusable together with the recurrece

    """

    response = get(urlparse(url)._replace(query='type=ical').geturl())
    response.raise_for_status()

    for event in vCalendar.from_ical(response.text).walk('vevent'):
        start = event.get('dtstart').dt
        if type(start) is date:
            start = replace_timezone(as_datetime(start), timezone)
        elif type(start) is datetime:
            if start.tzinfo is None:
                start = standardize_date(start, timezone)
            else:
                start = to_timezone(start, UTC)

        end = event.get('dtend').dt
        if type(end) is date:
            end = replace_timezone(as_datetime(end), timezone)
            end = end + timedelta(days=1, minutes=-1)
        elif type(end) is datetime:
            if end.tzinfo is None:
                end = standardize_date(end, timezone)
            else:
                end = to_timezone(end, UTC)

        return start, end


@cli.command('import-json')
@pass_group_context
@click.argument('url')
@click.option('--tagmap', type=click.File())
@click.option('--clear/-no-clear', default=False)
def import_json(group_context, url, tagmap, clear):
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

        if clear:
            click.secho("Removing all events", fg='yellow')
            session = app.session()
            for event in session.query(Event):
                session.delete(event)
            for occurrence in session.query(Occurrence):
                session.delete(occurrence)

        for item in response:
            title = item['title']

            start = parse(item['start'])
            end = parse(item['end'])
            timezone = item['timezone']
            recurrence = item['recurrence']
            if recurrence:
                start, end = get_event_dates(item['url'], timezone)

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

            description = '\n\n'.join((line for line in (
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
                timezone=timezone,
                description=description,
                organizer=organizer,
                location=location,
                coordinates=coordinates,
                tags=tags or [],
                meta={'submitter_email': item['submitter_email']},
            )

            # if the recurrence rule is not supported, turn it into a
            # list of rdates
            try:
                event.validate_recurrence('recurrence', recurrence)
            except RuntimeError:
                event.recurrence = as_rdates(recurrence, start)
                if not event.recurrence:
                    raise RuntimeError(f"Could not convert '{recurrence}'")
            else:
                event.recurrence = recurrence

            if item['images']:
                buffer = download_image(item['images'][0]['url'])

                if buffer:
                    filename = item['images'][0]['name'] or 'event-image'
                    event.image = EventFile(
                        name=filename,
                        reference=as_fileintent(buffer, filename)
                    )

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
            collection = EventCollection(app.session())
            updated = dict(collection.query().with_entities(
                Event.meta['source'].astext,
                Event.meta['source_updated'].astext,
            ))

            root = etree.fromstring(response.text.encode('utf-8'))

            def items(unknown_tags):
                for offer in GuidleExportData(root).offers():
                    source = f'{prefix}-{offer.uid}.0'
                    if offer.last_update == updated.get(source):
                        # Do not download the images and parse all the fields
                        # if nothing has changed since the last import. Only
                        # provide some dummy events with the source set so
                        # that the purging will work!
                        for index, schedule in enumerate(offer.schedules()):
                            yield EventImportItem(
                                event=Event(
                                    source=f'{prefix}-{offer.uid}.{index}',
                                    source_updated=offer.last_update
                                ),
                                image=None,
                                filename=None
                            )
                        continue

                    tags, unknown = offer.tags(tagmap)
                    unknown_tags |= unknown

                    image = None
                    filename = None
                    if isinstance(app, DepotApp):
                        image_url = offer.image_url(size='original')
                        if image_url:
                            image = download_image(image_url)
                            filename = image_url.rsplit('/', 1)[-1]

                    for index, schedule in enumerate(offer.schedules()):
                        event = Event(
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
                            source=f'{prefix}-{offer.uid}.{index}',
                            source_updated=offer.last_update
                        )

                        if image:
                            image.seek(0)

                        yield EventImportItem(
                            event=event,
                            image=image,
                            filename=filename
                        )

                    if image:
                        image.close()

            added, updated, purged = collection.from_import(
                items(unknown_tags),
                prefix
            )

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

        def event_file(reference):
            # XXX use a proper depot manager for this
            path = Path(app.depot_storage_path) / reference['path'] / 'file'
            with open(path):
                content = BytesIO(path.open('rb').read())
            return content

        try:
            result = [0, 0, 0]

            for key in source:
                remote_schema = '{}-{}'.format(app.namespace, key)
                local_schema = app.session_manager.current_schema
                assert remote_schema in app.session_manager.list_schemas()

                app.session_manager.set_current_schema(remote_schema)
                remote_session = app.session_manager.session()
                assert remote_session.info['schema'] == remote_schema

                query = remote_session.query(Event)
                query = query.filter(
                    or_(
                        Event.meta['source'].astext.is_(None),
                        Event.meta['source'].astext == ''
                    )
                )
                if tag:
                    query = query.filter(Event._tags.has_any(array(tag)))
                if location:
                    query = query.filter(
                        or_(*[
                            Event.location.ilike(f'%{term}%')
                            for term in location
                        ])
                    )

                def remote_events():
                    for event in query:
                        yield EventImportItem(
                            event=Event(
                                state='initiated',
                                title=event.title,
                                start=event.start,
                                end=event.end,
                                timezone=event.timezone,
                                recurrence=event.recurrence,
                                content=event.content,
                                location=event.location,
                                tags=event.tags,
                                source=f'fetch-{key}-{event.name}',
                                coordinates=event.coordinates,
                            ),
                            image=(
                                event_file(event.image.reference)
                                if event.image else None
                            ),
                            filename=event.image.name if event.image else None
                        )

                # be sure to switch back to the local schema, lest we
                # accidentally update things on the remote
                app.session_manager.set_current_schema(local_schema)
                local_events = EventCollection(app.session_manager.session())

                result = vector_add(
                    result,
                    local_events.from_import(remote_events(), f'fetch-{key}')
                )

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
