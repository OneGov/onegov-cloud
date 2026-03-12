from __future__ import annotations

from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.event.models.mixins import OccurrenceMixin
from onegov.gis import Coordinates
from pytz import UTC
from sedate import to_timezone
from sedate import utcnow
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.event.models import Event


class Occurrence(Base, OccurrenceMixin, TimestampMixin):
    """ Defines an occurrence of an event. """

    __tablename__ = 'event_occurrences'

    #: Internal number of the occurence
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: Event this occurrence belongs to
    event_id: Mapped[UUID] = mapped_column(ForeignKey('events.id'))
    event: Mapped[Event] = relationship(back_populates='occurrences')

    def as_ical(self, url: str | None = None) -> bytes:
        """ Returns the occurrence as iCalendar string. """

        modified = self.modified or self.created or utcnow()
        event = self.event

        vevent = vEvent()
        vevent.add('uid', f'{self.name}@onegov.event')
        vevent.add('summary', self.title)
        vevent.add('dtstart', to_timezone(self.start, UTC))
        vevent.add('dtend', to_timezone(self.end, UTC))
        vevent.add('last-modified', modified)
        vevent.add('dtstamp', modified)
        vevent.add('location', self.location)
        vevent.add('description', event.description)
        vevent.add('categories', event.tags)
        if event.coordinates:
            assert isinstance(event.coordinates, Coordinates)
            vevent.add('geo', (event.coordinates.lat, event.coordinates.lon))
        if url:
            vevent.add('url', url)

        vcalendar = vCalendar()
        vcalendar.add('prodid', '-//OneGov//onegov.event//')
        vcalendar.add('version', '2.0')
        vcalendar.add_component(vevent)
        return vcalendar.to_ical()

    @property
    def access(self) -> str:
        return self.event.access
