from datetime import datetime
from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.event.models.mixins import OccurrenceMixin
from pytz import UTC
from sedate import to_timezone
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from uuid import uuid4


class Occurrence(Base, OccurrenceMixin, TimestampMixin):
    """ Defines an occurrence of an event. """

    __tablename__ = 'event_occurrences'

    #: Internal number of the occurence
    id = Column(UUID, primary_key=True, default=uuid4)

    #: Event this occurrence belongs to
    event_id = Column(UUID, ForeignKey('events.id'), nullable=False)

    def as_ical(self, url=None):
        """ Returns the occurrence as iCalendar string. """

        modified = self.modified or self.created or datetime.utcnow()
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
            vevent.add('geo', (event.coordinates.lat, event.coordinates.lon))
        if url:
            vevent.add('url', url)

        vcalendar = vCalendar()
        vcalendar.add('prodid', '-//OneGov//onegov.event//')
        vcalendar.add('version', '2.0')
        vcalendar.add_component(vevent)
        return vcalendar.to_ical()
