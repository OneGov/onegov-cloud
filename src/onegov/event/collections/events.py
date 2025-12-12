from __future__ import annotations

import hashlib

from datetime import date
from datetime import datetime
from datetime import timedelta

import click
import logging
import requests

from dateutil.parser import parse
from html import unescape

from icalendar import Calendar as vCalendar
from icalendar.prop import vCategory
from io import BytesIO
from lxml import etree
from lxml.etree import SubElement, CDATA
from markupsafe import escape
from onegov.core.collection import Pagination
from onegov.core.html import html_to_text
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.event.models import Event
from onegov.gis import Coordinates
from pytz import UTC
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sedate import to_timezone
from sedate import utcnow
from sqlalchemy import and_
from sqlalchemy import or_
from uuid import uuid4

from typing import Any
from typing import IO
from typing import NamedTuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from onegov.core.request import CoreRequest
    from onegov.event.models.event import EventState
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self, IO
    from uuid import UUID

log = logging.getLogger('onegov.org.events')


class EventImportItem(NamedTuple):
    event: Event
    image: IO[bytes] | None
    image_filename: str | None
    pdf: IO[bytes] | None
    pdf_filename: str | None


class EventCollection(Pagination[Event]):
    """ Manage a list of events. """

    def __init__(
        self,
        session: Session,
        page: int = 0,
        state: EventState | None = None
    ) -> None:

        super().__init__(page)
        self.session = session
        self.state = state

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.state == other.state
            and self.page == other.page
        )

    def subset(self) -> Query[Event]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index, self.state)

    def for_state(self, state: EventState | None) -> Self:
        """ Returns a new instance of the collection with the given state. """

        return self.__class__(self.session, 0, state)

    def query(self) -> Query[Event]:
        query = self.session.query(Event)
        if self.state:
            query = query.filter(Event.state == self.state)
        query = query.order_by(Event.start)
        return query

    def _get_unique_name(self, name: str) -> str:
        """ Create a unique, URL-friendly name. """

        # it's possible for `normalize_for_url` to return an empty string...
        name = normalize_for_url(name) or 'event'

        session = self.session
        while session.query(Event.name).filter(Event.name == name).first():
            name = increment_name(name)

        return name

    def add(
        self,
        title: str,
        start: datetime,
        end: datetime,
        timezone: str,
        autoclean: bool = True,
        **optional: Any
    ) -> Event:
        """ Add a new event.

        A unique, URL-friendly name is created automatically for this event
        using the title and optionally numbers for duplicate names.

        Every time a new event is added, old, stale events are deleted unless
        disabled with the ``autoclean`` option.

        Returns the created event or None if already automatically deleted.
        """
        if not start.tzinfo:
            start = replace_timezone(start, timezone)
        if not end.tzinfo:
            end = replace_timezone(end, timezone)

        event = Event(
            state='initiated',
            title=title,
            start=start,
            end=end,
            timezone=timezone,
            name=self._get_unique_name(title),
            **optional
        )

        self.session.add(event)
        self.session.flush()

        if autoclean:
            self.remove_stale_events()

        return event

    def delete(self, event: Event) -> None:
        """ Delete an event. """

        self.session.delete(event)
        self.session.flush()

    def remove_stale_events(self, max_stale: datetime | None = None) -> None:
        """ Remove events which have never been submitted and are created more
        than five days ago.

        """

        if max_stale is None:
            max_stale = utcnow() - timedelta(days=5)

        events = self.session.query(Event).filter(
            Event.state == 'initiated',
            and_(
                or_(Event.created < max_stale, Event.created.is_(None)),
                or_(Event.modified < max_stale, Event.modified.is_(None))
            )
        )
        for event in events:
            self.session.delete(event)

        self.session.flush()

    def by_name(self, name: str) -> Event | None:
        """ Returns an event by its URL-friendly name. """

        query = self.session.query(Event).filter(Event.name == name)
        return query.first()

    def by_id(self, id: UUID) -> Event | None:
        """ Return an event by its id. Hex representations work as well. """
        query = self.session.query(Event).filter(Event.id == id)
        return query.first()

    def from_import(
        self,
        items: Iterable[EventImportItem | str],
        to_purge: list[str] | None = None,
        publish_immediately: bool = True,
        valid_state_transfers: Mapping[str, str] | None = None,
        published_only: bool = False,
        future_events_only: bool = False
    ) -> tuple[list[Event], list[Event], list[UUID]]:
        """ Add or updates the given events.

        Only updates events which have changed. Uses ``Event.source_updated``
        if available, falls back to comparing all relevant attributes.

        Doesn't change the states of events allowing to permanently withdraw
        imported events.

        :param items:
            A list of ``EventImportItem``'s or event sources to keep
            from purging.

        :param to_purge:
            Optionally removes all events with the given meta-source-prefix not
            present in the given events.

        :param publish_immediately:
            Set newly added events to published, else let them be initiated.

        :param valid_state_transfers:
            Dict of existing : remote state should be considered when updating.

            Example:

            {'published': 'withdrawn'} would update locally published events
            if the remote has been withdrawn.

            for any {'valid_state': 'withdrawn'} that lead to an update of
            the local state, an existing ticket will be close automatically.

            Be aware, that transferring state and creating tickets might lead
            to inconsistencies. So adjust the script in that case to handle
            the tickets automatically.

        :param published_only:
            Do not import unpublished events. Still do not ignore state
            like withdrawn.

        :param future_events_only:
            If set only events in the future will be imported
        """

        purged = set()
        for purge_id in to_purge or []:
            query = self.session.query(Event.meta['source'].label('source'))
            query = query.filter(
                Event.meta['source'].astext.startswith(purge_id))
            purged.update([r.source for r in query])

        added = []
        updated = []
        valid_state_transfers = valid_state_transfers or {}

        for item in items:
            if isinstance(item, str):
                purged = {x for x in purged if not x.startswith(item)}
                continue

            # skip past events if option is set
            if future_events_only and item.event.end < utcnow():
                continue

            event = item.event
            existing = self.session.query(Event).filter(
                Event.meta['source'] == event.meta['source']
            ).first()

            if to_purge:
                purged -= {event.source}

            if existing:
                update_state = valid_state_transfers.get(
                    existing.state) == event.state

                if existing.source_updated:
                    changed = existing.source_updated != event.source_updated
                else:
                    # No information on provided, figure it out ourselves!
                    image_changed = (
                        (existing.image and not item.image)
                        or (not existing.image and item.image)
                    )
                    if existing.image and item.image:
                        image_changed = (
                            existing.image.checksum
                            != hashlib.new(
                                'md5',
                                item.image.read(),
                                usedforsecurity=False
                            ).hexdigest()
                        )
                        item.image.seek(0)
                    changed = True if (
                        existing.title != event.title
                        or existing.location != event.location
                        or set(existing.tags) != set(event.tags)
                        or existing.filter_keywords != event.filter_keywords
                        or existing.timezone != event.timezone
                        or existing.start != event.start
                        or existing.end != event.end
                        or existing.content != event.content
                        or existing.coordinates != event.coordinates
                        or existing.recurrence != event.recurrence
                        or image_changed
                    ) else False

                if changed:
                    state = existing.state  # avoid updating occurrences
                    existing.state = 'initiated'
                    existing.title = event.title
                    existing.location = event.location
                    existing.tags = event.tags
                    existing.filter_keywords = event.filter_keywords
                    existing.timezone = event.timezone
                    existing.start = event.start
                    existing.end = event.end
                    existing.content = event.content
                    existing.coordinates = event.coordinates
                    existing.recurrence = event.recurrence
                    existing.state = state
                    existing.set_image(item.image, item.image_filename)
                    existing.set_pdf(item.pdf, item.pdf_filename)
                if update_state:
                    existing.state = event.state

                if changed or update_state:
                    updated.append(existing)

            else:
                if published_only and event.state != 'published':
                    continue
                event.id = uuid4()
                event.name = self._get_unique_name(event.title)
                event.state = 'initiated'
                event.set_image(item.image, item.image_filename)
                event.set_pdf(item.pdf, item.pdf_filename)
                self.session.add(event)
                if publish_immediately:
                    event.submit()
                    event.publish()
                added.append(event)

        purged_event_ids = []
        if purged:
            query = self.session.query(Event)
            query = query.filter(Event.meta['source'].in_(purged))
            for event in query:
                event.state = 'withdrawn'  # remove occurrences
                purged_event_ids.append(event.id)
                self.session.delete(event)

        self.session.flush()

        return added, updated, purged_event_ids

    def from_ical(
        self,
        ical: str,
        future_events_only: bool = False,
        event_image: IO[bytes] | None = None,
        event_image_name: str | None = None,
        default_categories: list[str] | None = None,
        default_filter_keywords: dict[str, list[str]] | None = None
    ) -> tuple[list[Event], list[Event], list[UUID]]:
        """ Imports the events from an iCalender string.

        We assume the timezone to be Europe/Zurich!
        :param ical: ical to be imported
        :type ical: str
        :param future_events_only: if set only events in the future will be
        imported
        :type future_events_only: bool
        :param event_image: image file
        :param event_image_name: image name
        :type event_image_name: str
        :param default_categories: categories applied if non is given in ical
        :type default_categories: [str]
        :param default_filter_keywords: default filter keywords, see event
        filter settings app.org.event_filter_type
        :type default_filter_keywords: dict(str, [str] | None)

        """
        items = []

        if default_categories:
            assert isinstance(default_categories, list)

        cal = vCalendar.from_ical(ical)
        for vevent in cal.walk('vevent'):
            timezone = 'Europe/Zurich'
            start = vevent.get('dtstart')
            start = start.dt if start else None
            if type(start) is date:
                start = replace_timezone(as_datetime(start), timezone)
            elif type(start) is datetime:
                if start.tzinfo is None:
                    start = standardize_date(start, timezone)
                else:
                    start = to_timezone(start, UTC)

            end = vevent.get('dtend')
            end = end.dt if end else None
            if type(end) is date:
                end = replace_timezone(as_datetime(end), timezone)
                end = end + timedelta(days=1, minutes=-1)
            elif type(end) is datetime:
                if end.tzinfo is None:
                    end = standardize_date(end, timezone)
                else:
                    end = to_timezone(end, UTC)

            duration = vevent.get('duration')
            duration = duration.dt if duration else None
            if start and not end and duration:
                end = start + duration

            if start and not end:
                # assume event duration is 1 hour
                end = start + timedelta(hours=1)

            if not start or not end:
                raise (ValueError('Invalid date'))

            recurrence = vevent.get('rrule', '')
            if recurrence:
                recurrence = 'RRULE:{}'.format(recurrence.to_ical().
                                               decode())

            coordinates = vevent.get('geo')
            if coordinates:
                coordinates = Coordinates(
                    coordinates.latitude, coordinates.longitude
                )

            if default_categories is None:
                default_categories = []
            tags = (vevent.get('categories') or vCategory(default_categories))
            if tags:
                # categories may be in lists or they may be single values
                # whose 'cats' member contains the texts
                if (
                    not hasattr(tags, '__iter__')
                    # v6 added an __iter__ method to vCategory
                    # but it's not what we want to ierate over
                    or isinstance(tags, vCategory)
                ):
                    tags = [tags]

                tags = [
                    str(c)
                    for tag in tags
                    for c in tag.cats
                    if c
                ]

            uid = str(vevent.get('uid', ''))
            title = str(escape(vevent.get('summary', '')))
            description = str(escape(vevent.get('description', '')))
            organizer = str(escape(vevent.get('organizer', '')))
            location = str(escape(vevent.get('location', '')))

            items.append(
                EventImportItem(
                    event=Event(  # type:ignore[misc]
                        state='initiated',
                        title=title,
                        start=start,
                        end=end,
                        timezone=timezone,
                        recurrence=recurrence,
                        description=description,
                        organizer=organizer,
                        location=location,
                        coordinates=coordinates,
                        tags=tags or [],
                        filter_keywords=default_filter_keywords,
                        source=f'ical-{uid}',
                    ),
                    image=event_image,
                    image_filename=event_image_name,
                    pdf=None,
                    pdf_filename=None,
                )
            )

        return self.from_import(items, publish_immediately=True,
                                future_events_only=future_events_only)

    def from_minasa(
        self,
        xml_stream: bytes,
    ) -> tuple[list[Event], list[Event], list[UUID]]:
        locations = {}
        organizers = {}
        items = []
        items_to_purge = []
        source_ids = []
        h2t_config = {'ignore_emphasis': True}

        root = etree.fromstring(xml_stream)
        ns = {'ns': 'https://minasa.ch/schema/v1'}

        def rdate_from_single_dates(dates: list[datetime]) -> str | None:
            """
            Transforms a list of start dates into a RDATE string.
            Returns a string with the RDATE's for the given dates.

            Example for two recurrence dates:
                'RDATE:20250501T120000Z
                 RDATE:20250508T120000Z'
            """
            if not dates:
                return None

            return '\n'.join(
                f'RDATE:{to_timezone(start, "UTC"):%Y%m%dT%H%M%SZ}'
                for start in dates
            )

        def find_element_text(parent: etree._Element, key: str) -> str:
            element = parent.find(f'ns:{key}', namespaces=ns)
            if element is not None:
                return unescape(element.text or '')

            return ''

        def get_event_image(
                event: etree._Element
        ) -> tuple[IO[bytes] | None, str | None]:
            url = find_element_text(event, 'imageUrl')

            if not url:
                return None, None

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                image_steam = BytesIO(response.content)
                return image_steam, url.split('/')[-1]
            except requests.RequestException:
                log.exception(
                    f'Failed to retrieve event image from {url}')
                return None, None

        for location in root.xpath('//ns:location', namespaces=ns):
            uuid7 = find_element_text(location, 'uuid7')
            address = location.find('ns:address', namespaces=ns)
            title = find_element_text(address, 'title')
            street = find_element_text(address, 'street')
            zip = find_element_text(address, 'zip')
            city = find_element_text(address, 'city')
            url = find_element_text(address, 'url')
            lat = find_element_text(address, 'latitude')
            lon = find_element_text(address, 'longitude')
            locations[uuid7] = {
                'title': title,
                'street': street,
                'zip': zip,
                'city': city,
                'url': url,
                'lat': lat,
                'lon': lon,
            }

        for organizer in root.xpath('//ns:organizer', namespaces=ns):
            uuid7 = find_element_text(organizer, 'uuid7')
            address = organizer.find('ns:address', namespaces=ns)
            title = find_element_text(address, 'title')
            phone = find_element_text(address, 'phone')
            email = find_element_text(address, 'email')
            organizers[uuid7] = {
                'title': title,
                'phone': phone,
                'email': email,
            }

        for event in root.xpath('//ns:event', namespaces=ns):
            title = find_element_text(event, 'title')
            abstract = find_element_text(event, 'abstract')
            description = find_element_text(event, 'description')
            description = (
                html_to_text(description, **h2t_config)) if description else ''
            if abstract:
                description = f'{abstract}\n\n{description}'

            organizer_id = find_element_text(event, 'organizerUuid7')

            location_id = find_element_text(event, 'locationUuid7')
            location_data = locations.get(location_id, {})
            location = ', '.join(
                location_data[i] for i in ['title', 'street', 'zip', 'city']
                if i in location_data
            )
            coordinates = None
            if (location_data.get('lat', None) and
                    location_data.get('lon', None)):
                coordinates = Coordinates(
                    lat=float(location_data['lat']),
                    lon=float(location_data['lon'])
                )
            event_image, event_image_name = get_event_image(event)

            ticket_price = find_element_text(event, 'ticketPrice')
            event_url = find_element_text(event, 'originalEventUrl') or ''

            provider_url = ''
            provider_ref = event.find('ns:providerReference', namespaces=ns)
            if provider_ref is not None:
                provider_url = find_element_text(provider_ref, 'url')

            tags = []
            category = event.find('ns:category', namespaces=ns)
            if category is not None:
                tag = find_element_text(category, 'mainCategory')
                tags.append(tag) if tag else None

            timezone = 'Europe/Zurich'
            for schedule in event.find('ns:schedules', namespaces=ns):
                schedule_id = find_element_text(schedule, 'uuid7')
                start = parse(find_element_text(schedule, 'start'))
                end_text = find_element_text(schedule, 'end')
                end = (parse(end_text) if end_text else
                       start + timedelta(hours=2))

                recurrence_start_dates: list[datetime] = []
                recurrence = schedule.find('ns:recurrence', namespaces=ns)
                frequency = find_element_text(recurrence, 'frequency')

                event_status = find_element_text(schedule, 'eventStatus')
                if event_status == 'deleted':
                    items_to_purge.append(schedule_id)
                    continue  # skip from importing otherwise no purge

                if frequency == 'single':
                    pass

                elif frequency in ['daily', 'weekly']:
                    interval = int(find_element_text(recurrence, 'interval'))
                    until = parse(find_element_text(recurrence, 'until'))

                    if until.tzinfo is None:
                        until = until.replace(tzinfo=start.tzinfo)

                    delta = (
                        timedelta(days=interval)
                        if frequency == 'daily'
                        else timedelta(weeks=interval)
                    )
                    current_start = start + delta
                    while current_start <= until:
                        recurrence_start_dates.append(current_start)
                        current_start += delta

                else:
                    log.error(
                        'Error unhandled recurrence type:', frequency)

                recurrence = (
                    rdate_from_single_dates(recurrence_start_dates))

                # Importing each single schedule, recurrence within a schedule
                # will link the different occurrences using the schedule id.
                # Multiple 'single' frequency schedule lead to single events.
                items.append(
                    EventImportItem(
                        event=Event(  # type:ignore[misc]
                            state='published',
                            title=title,
                            start=start,
                            end=end,
                            timezone=timezone,
                            recurrence=recurrence,
                            description=description,
                            organizer=organizers.get(
                                organizer_id, {}).get('title', ''),
                            organizer_email=organizers.get(
                                organizer_id, {}).get('email', ''),
                            organizer_phone=organizers.get(
                                organizer_id, {}).get('phone', ''),
                            location=location,
                            coordinates=coordinates,
                            price=ticket_price,
                            external_event_url=event_url or provider_url,
                            tags=tags,
                            filter_keywords=None,
                            source=schedule_id,
                        ),
                        image=event_image,
                        image_filename=event_image_name,
                        pdf=None,
                        pdf_filename=None,
                    )
                )

                source_ids.append(schedule_id)

        # ogc-2447 imported events with source ids not in this `xml_stream`
        # can be removed to prevent duplicates as the xml stream represents
        # a complete set of events
        for event in (
                self.session.query(Event)
                .filter(Event.source.notin_(source_ids))):  # type:ignore[union-attr]
            if event.source:
                items_to_purge.append(event.source)
                click.echo(f' - removing event as not in xml stream '
                           f'{event.title} {event.start}')

        return self.from_import(
            items,
            to_purge=items_to_purge,
            publish_immediately=True,
            future_events_only=False
        )

    def as_anthrazit_xml(
        self,
        request: CoreRequest,
        future_events_only: bool = True
    ) -> str:
        """
        Returns all published occurrences as xml for Winterthur.
        Anthrazit format according
        https://doc.anthrazit.org/ext/XML_Schnittstelle::

            <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <import partner="???" partnerid"???" passwort"???" importid="??">
                <item status="1" suchbar="1"
                      mutationsdatum="2023-08-18 08:23:30">
                    <id>01</id>
                    <titel>Titel der Seite</titel>
                    <textmobile>2-3 Sätze des Text Feldes packed in
                    CDATA</textmobile>
                    <termin allday="1">
                        <von>2011-08-06 00:00:00</von>
                        <bis>2011-08-06 23:59:00</bis>
                    </termin>
                    <termin>
                        ...
                    </termin>
                    <url_web>url</url_web>
                    <url_bild>bild</url_bild>
                    <hauptrubrik name="Naturmusuem">
                        <rubrik>tag_1</rubrik>
                        <rubrik>tag_2</rubrik>
                    </hauptrubrik>
                    <email></email>
                    <telefon1></telefon1>
                    <sf01>Veranstaltungspreis packed in CDATA</sf01>
                    <veranstaltungsort>
                        <title></title>
                        <longitude></longitude>
                        <latitude></latitude>
                    </veranstaltungsort>
                    ...
                </item>
                <item>
                    ...
                </item>
            </import>

        :param future_events_only: if set, only future events will be
            returned, all events otherwise
        :rtype: str
        :return: xml string

        """
        xml = ('<import partner="" partnerid="" passwort="" importid="">'
               '</import>')
        root = etree.XML(xml)

        query = self.session.query(Event)
        for e in query:
            if e.state != 'published':
                continue
            if future_events_only and not e.future_occurrences().all():
                continue

            last_change = e.last_change.strftime('%Y-%m-%d %H:%M:%S')
            event = SubElement(root, 'item', attrib={
                'status': '1',
                'suchbar': '1',
                'mutationsdatum': last_change,
            })

            id = SubElement(event, 'id')
            id.text = str(e.id)

            title = SubElement(event, 'titel')
            title.text = e.title

            text_mobile = SubElement(event, 'textmobile')
            if e.description:
                desc = e.description
                if len(e.description) > 10000:
                    desc = e.description[:9995] + '..'
                text_mobile.text = CDATA(
                    desc.replace('\r\n', '<br>'))

            for occ in e.occurrences:
                termin = SubElement(event, 'termin')
                event_start = SubElement(termin, 'von')
                event_start.text = (
                    str(occ.localized_start.replace(tzinfo=None)))
                event_end = SubElement(termin, 'bis')
                event_end.text = str(occ.localized_end.replace(tzinfo=None))

            if e.price:
                price = SubElement(event, 'sf01')
                price.text = CDATA(
                    e.price.replace('\r\n', '<br>'))

            if e.external_event_url:
                url = SubElement(event, 'url_web')
                url.text = e.external_event_url

            if e.event_registration_url:
                registration = SubElement(event, 'url_web')
                registration.text = e.event_registration_url

            if e.image:
                image = SubElement(event, 'url_bild')
                image.text = request.link(e.image)

            hr_text = ''
            tags = []
            if e.tags:
                tags = e.tags
            if e.filter_keywords:
                for k, v in e.filter_keywords.items():
                    if k == 'kalender':
                        assert isinstance(v, str)
                        hr_text = v
                    else:
                        if isinstance(v, list):
                            tags.extend(v)
                        else:
                            tags.append(v)
                top_category = SubElement(event, 'hauptrubrik',
                                          attrib={'name': hr_text} if
                                          hr_text else None)
            for tag in tags:
                category = SubElement(top_category, 'rubrik')
                category.text = tag

            if e.organizer_email:
                email = SubElement(event, 'email')
                email.text = e.organizer_email

            if e.organizer_phone:
                phone = SubElement(event, 'telefon1')
                phone.text = e.organizer_phone

            location = SubElement(event, 'veranstaltungsort')
            location_title = SubElement(location, 'titel')
            location_title.text = e.location

            if e.coordinates:
                assert isinstance(e.coordinates, Coordinates)
                longitude = SubElement(location, 'longitude')
                longitude.text = str(e.coordinates.lon)
                latitude = SubElement(location, 'latitude')
                latitude.text = str(e.coordinates.lat)

        return etree.tostring(root,
                              encoding='utf-8',
                              xml_declaration=True,
                              pretty_print=True).decode()
