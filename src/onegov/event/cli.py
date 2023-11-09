import click
import hashlib
import pycurl

from csv import reader as csvreader
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
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
from pytz import UTC
from requests import get
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sedate import to_timezone
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


def download_file(file_url, size_limit=1 * 1024 * 1024):
    buffer = BytesIO()
    received = 0
    cancelled = False

    def guarded_write(data):
        nonlocal received
        received += len(data)

        if received > size_limit:
            nonlocal cancelled
            cancelled = True
            return 0

        return buffer.write(data)

    c = pycurl.Curl()
    c.setopt(c.URL, file_url)
    c.setopt(c.WRITEFUNCTION, guarded_write)
    c.setopt(c.FOLLOWLOCATION, True)

    try:
        c.perform()

        if c.getinfo(c.RESPONSE_CODE) != 200:
            return None

    except pycurl.error:
        if cancelled:
            return None

        raise

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

    response = get(
        urlparse(url)._replace(query='type=ical').geturl(),
        timeout=60
    )
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

        response = get(url, timeout=60)
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
                item['contact_phone'] or ''
            ) if line))

            organizer_email = item['contact_email'] or None
            organizer_phone = item['contact_phone'] or None

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
                item['registration']
            ) if line))

            price = item['prices'] or None

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

            # special case for Steinhausen, may be deleted by whoever reads
            # this comment next
            if 'cat2' in item and 'Im Dreiklang' in item['cat2']:
                if 'Im Dreiklang'.lower() not in location.lower():
                    location = f'Im Dreiklang, {location}'

            event = Event(
                state='initiated',
                name=events._get_unique_name(title),
                title=title,
                start=start,
                end=end,
                timezone=timezone,
                description=description,
                organizer=organizer,
                organizer_email=organizer_email,
                organizer_phone=organizer_phone,
                location=location,
                coordinates=coordinates,
                price=price,
                tags=tags or [],
                meta={'submitter_email': item['submitter_email']},
            )

            # if the recurrence rule is not supported, turn it into a
            # list of rdates
            try:
                event.validate_recurrence('recurrence', recurrence)
            except RuntimeError as exception:
                event.recurrence = as_rdates(recurrence, start)
                if not event.recurrence:
                    raise RuntimeError(
                        f"Could not convert '{recurrence}'"
                    ) from exception
            else:
                event.recurrence = recurrence

            if item['images']:
                buffer = download_file(item['images'][0]['url'])

                if buffer:
                    filename = item['images'][0]['name'] or 'event-image'
                    event.image = EventFile(
                        name=filename,
                        reference=as_fileintent(buffer, filename)
                    )

            if item['attachements']:
                buffer = download_file(item['attachements'][0]['url'])

                if buffer:
                    filename = item['attachements'][0]['name'] or 'attachment'
                    event.pdf = EventFile(
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
@click.option('--future-events-only', is_flag=True, default=False)
@click.option('--event-image', type=click.File('rb'))
@click.option("--cat", "-c", 'categories', type=str, multiple=True)
@click.option("--fil", "-f", 'keyword_filters', type=(str, str),
              multiple=True)
def import_ical(group_context, ical, future_events_only=False,
                event_image=None, categories=None, keyword_filters=None):
    """ Imports events from an iCalendar file.

    Example:

        onegov-event --select '/veranstaltungen/zug' import-ical import.ics

        onegov-event --select '/veranstaltungen/zug' import-ical import.ics
        --future-events-only

        onegov-event --select '/veranstaltungen/zug' import-ical import.ics
        --event-image /path/to/image.jpg

        onegov-event --select /onegov_winterthur/winterthur import-ical
        ./basic.ics --future-events-only --event-image
        ~/Veranstaltung_breit.jpg -c Sport -c Fussball

        onegov-event --select /onegov_winterthur/winterthur import-ical
        ./basic.ics --future-events-only --event-image
        ~/Veranstaltung_breit.jpg -f "kalender" "Sport Veranstaltungskalender"

    """
    cat = list(categories)
    filters = dict(keyword_filters)

    def _import_ical(request, app):
        collection = EventCollection(app.session())
        added, updated, purged = collection.from_ical(
            ical.read(), future_events_only, event_image,
            default_categories=cat, default_filter_keywords=filters,
        )
        click.secho(
            f"Events successfully imported "
            f"({len(added)} added, {len(updated)} updated, "
            f"{len(purged)} deleted)",
            fg='green')

    return _import_ical


@cli.command('import-guidle')
@pass_group_context
@click.argument('url')
@click.option('--tagmap', type=click.File())
@click.option('--clear', is_flag=True, default=False)
def import_guidle(group_context, url, tagmap, clear):
    """ Fetches the events from guidle.

    Example:

        onegov-event --select '/veranstaltungen/zug' import-guidle \
        'http://www.guidle.com/xxxx/'

    """
    if tagmap:
        tagmap = {row[0]: row[1] for row in csvreader(tagmap)}

    def _import_guidle(request, app):
        try:
            response = get(url, timeout=300)
            response.raise_for_status()

            unknown_tags = set()
            prefix = 'guidle-{}'.format(
                hashlib.new(
                    'sha1',
                    url.encode(),
                    usedforsecurity=False
                ).hexdigest()[:10]
            )
            collection = EventCollection(app.session())

            if clear:
                events = request.session.query(Event)\
                    .filter(Event.meta['source'].astext.startswith(prefix))

                for event in events:
                    request.session.delete(event)

                request.session.flush()

            updated = dict(collection.query().with_entities(
                Event.meta['source'].astext,
                Event.meta['source_updated'].astext,
            ))

            root = etree.fromstring(response.text.encode('utf-8'))

            def items(unknown_tags):
                for offer in GuidleExportData(root).offers():
                    source = f'{prefix}-{offer.uid}.0'
                    if offer.last_update == updated.get(source):
                        # Nothing has changed, just provide the source prefix
                        # to prevent the related events from being purged
                        yield f'{prefix}-{offer.uid}'
                        continue

                    tags, unknown = offer.tags(tagmap)
                    unknown_tags |= unknown

                    image = None
                    image_filename = None

                    pdf = None
                    pdf_filename = None

                    if isinstance(app, DepotApp):
                        image_url, image_filename = offer.image(size='medium')

                        if image_url:
                            image = download_file(image_url)

                        pdf_url, pdf_filename = offer.pdf()

                        if pdf_url:
                            pdf = download_file(pdf_url)

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
                            organizer_email=offer.organizer_email,
                            price=offer.price,
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
                            image_filename=image_filename,
                            pdf=pdf,
                            pdf_filename=pdf_filename
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
                f"({len(added)} added, {len(updated)} updated, "
                f"{len(purged)} deleted)",
                fg='green'
            )
        except Exception as e:
            log.error("Error importing events", exc_info=True)
            raise (e)

    return _import_guidle
