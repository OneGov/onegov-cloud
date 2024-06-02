import hashlib

from uuid import uuid4
from datetime import date, timezone
from datetime import datetime
from datetime import timedelta
from icalendar import Calendar as vCalendar
from icalendar.prop import vCategory
from lxml import etree
from lxml.etree import SubElement, CDATA
from markupsafe import escape

from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.event.models import Event
from onegov.gis import Coordinates
from pytz import UTC
from sedate import as_datetime
from sedate import replace_timezone
from sedate import standardize_date
from sedate import to_timezone
from sqlalchemy import and_
from sqlalchemy import or_


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
    from typing_extensions import Self
    from uuid import UUID


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
        session: 'Session',
        page: int = 0,
        state: 'EventState | None' = None
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

    def subset(self) -> 'Query[Event]':
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> 'Self':
        return self.__class__(self.session, index, self.state)

    def for_state(self, state: 'EventState | None') -> 'Self':
        """ Returns a new instance of the collection with the given state. """

        return self.__class__(self.session, 0, state)

    def query(self) -> 'Query[Event]':
        query = self.session.query(Event)
        if self.state:
            query = query.filter(Event.state == self.state)
        query = query.order_by(Event.start)
        return query

    def _get_unique_name(self, name: str) -> str:
        """ Create a unique, URL-friendly name. """

        # it's possible for `normalize_for_url` to return an empty string...
        name = normalize_for_url(name) or "event"

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
            max_stale = datetime.utcnow() - timedelta(days=5)
            max_stale = standardize_date(max_stale, 'UTC')

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

    def by_id(self, id: 'UUID') -> Event | None:
        """ Return an event by its id. Hex representations work as well. """
        query = self.session.query(Event).filter(Event.id == id)
        return query.first()

    def from_import(
        self,
        items: 'Iterable[EventImportItem | str]',
        purge: str | None = None,
        publish_immediately: bool = True,
        valid_state_transfers: 'Mapping[str, str] | None' = None,
        published_only: bool = False,
        future_events_only: bool = False
    ) -> tuple[list[Event], list[Event], list['UUID']]:
        """ Add or updates the given events.

        Only updates events which have changed. Uses ``Event.source_updated``
        if available, falls back to comparing all relevant attributes.

        Doesn't change the states of events allowing to permanently withdraw
        imported events.

        :param items:
            A list of ``EventImportItem``'s or event sources to keep
            from purging.

        :param purge:
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

        if purge:
            query = self.session.query(Event.meta['source'].label('source'))
            query = query.filter(Event.meta['source'].astext.startswith(purge))
            purged = {r.source for r in query}
        else:
            purged = set()

        added = []
        updated = []
        valid_state_transfers = valid_state_transfers or {}

        for item in items:
            if isinstance(item, str):
                purged = {x for x in purged if not x.startswith(item)}
                continue

            # skip past events if option is set
            if future_events_only and (
                    item.event.end < datetime.now(timezone.utc)):
                continue

            event = item.event
            existing = self.session.query(Event).filter(
                Event.meta['source'] == event.meta['source']
            ).first()

            if purge:
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
                if published_only and not event.state == 'published':
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
        event_image: 'IO[bytes] | None' = None,
        event_image_name: str | None = None,
        default_categories: list[str] | None = None,
        default_filter_keywords: dict[str, list[str]] | None = None
    ) -> tuple[list[Event], list[Event], list['UUID']]:
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
                raise (ValueError("Invalid date"))

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
                if not hasattr(tags, '__iter__'):
                    tags = [tags]

                tags = [str(c) for tag in tags for c in tag.cats if c]

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

    def as_anthrazit_xml(
        self,
        request: 'CoreRequest',
        future_events_only: bool = True
    ) -> str:
        """
        Returns all published occurrences as xml for Winterthur.
        Anthrazit format according
        https://doc.anthrazit.org/ext/XML_Schnittstelle

        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <import partner="???" partnerid"???" passwort"???" importid="??">
            <item status="1" suchbar="1" mutationsdatum="2023-08-18 08:23:30">
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
                text_mobile.text = CDATA(  # type: ignore[assignment]
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
                price.text = CDATA(  # type: ignore[assignment]
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
                    if k in ['kalender']:
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
