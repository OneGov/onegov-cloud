import click

from csv import reader as csvreader
from dateutil.parser import parse
from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.event.collections import EventCollection
from onegov.event.models import Event
from onegov.event.models import Occurrence
from onegov.event.models.event import recurrence_to_dates
from onegov.gis import Coordinates
from requests import get

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

        events = []
        for item in response.json():
            uid = item['id']
            title = item['title']

            start = parse(item['start'])
            end = parse(item['end'])
            timezone = item['timezone']
            recurrence = item['recurrence']
            if recurrence:
                recurrence_to_dates(recurrence, start, timezone)

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
            # todo: handle item['cat1']

            coordinates = None
            if item['latitude'] and item['longitude']:
                coordinates = Coordinates(
                    lat=item['latitude'],
                    lon=item['longitude']
                )

            events.append(
                Event(
                    state='initiated',
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
                    meta={
                        'source': f'ical-{uid}',
                        'submitter_email': item['submitter_email']
                    },
                )
            )
            # todo: handle item['attachements']
            # todo: handle item['images']

        collection = EventCollection(app.session())
        collection.from_import(events)

        if unknown_tags:
            unknown_tags = ','.join(unknown_tags)
            click.secho(f"Tags not in tagmap: {unknown_tags}!", fg='yellow')

        click.secho(f"Imported/updated {len(events)} events", fg='green')

    return _import_json
