import click

from csv import reader as csvreader
from dateutil import rrule
from dateutil.parser import parse
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.event.collections import EventCollection
from onegov.event.models import Event
from onegov.event.models import Occurrence
from onegov.gis import Coordinates
from requests import get
from sedate import standardize_date

cli = command_group()


@cli.command('import-json')
@pass_group_context
@click.argument('url')
@click.option('--tagmap', type=click.File())
@click.option('--clear', default=False, is_flag=True)
def import_json(group_context, url, tagmap, clear):
    """ Fetches the events from a seantis.dir.events instance for migration. This
    command is intendet to be removed in the future.

    onegov-event --select '/towns/govikon' import-json
        https://veranstaltungen.zug.ch/veranstaltungen/?type=json&compact=true

    """
    if tagmap:
        tagmap = {row[0]: row[1] for row in csvreader(tagmap)}

    def _import_json(request, app):
        unknown_tags = set()

        response = get(url)
        response.raise_for_status()

        session = app.session()
        collection = EventCollection(session)

        if clear:
            for event in session.query(Event):
                session.delete(event)
            for occurrence in session.query(Occurrence):
                session.delete(occurrence)

        for item in response.json():
            try:
                start = parse(item['start'])
                end = parse(item['end'])
                recurrence = item['recurrence']
                timezone = item['timezone']
                assert all((start, end, timezone))
                if recurrence:
                    list(
                        map(
                            lambda x: standardize_date(x, timezone),
                            rrule.rrulestr(recurrence, dtstart=start)
                        )
                    )
            except (AssertionError, TypeError, ValueError) as e:
                click.secho(f"Skipping {item['url']}! ({e})", fg='red')
                continue

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
                item['url'] or '',  # todo: remove me!
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

            event = Event(state='initiated')
            event.name = collection._get_unique_name(item['title'])
            event.title = item['title']
            event.start = start
            event.end = end
            event.recurrence = recurrence
            event.timezone = timezone
            event.tags = tags
            event.description = description
            event.organizer = organizer
            event.location = location
            event.meta = event.meta or {}
            event.meta['submitter_email'] = item['submitter_email']
            event.state = 'published'
            # todo: handle item['attachements']
            # todo: handle item['images']
            if item['latitude'] and item['longitude']:
                event.coordinates = Coordinates(
                    lat=item['latitude'],
                    lon=item['longitude']
                )

            session.add(event)

        if unknown_tags:
            unknown_tags = ','.join(unknown_tags)
            click.secho(f"Tags not in tagmap: {unknown_tags}!", fg='yellow')

    return _import_json
