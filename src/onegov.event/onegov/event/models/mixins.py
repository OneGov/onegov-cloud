import icalendar

from datetime import datetime
from onegov.core.orm.types import UTCDateTime
from pytz import UTC
from sedate import to_timezone
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict


class OccurrenceMixin(object):
    """ Contains all attributes events and ocurrences share.

    The ``start`` and ``end`` date and times are stored in UTC - that is, they
    are stored internally without a timezone and are converted to UTC when
    getting or setting, see :class:`UTCDateTime`. Use the properties
    ``localized_start`` and ``localized_end`` to get the localized version of
    the date and times.
    """

    #: Title of the event
    title = Column(Text, nullable=False)

    #: A nice id for the url, readable by humans
    name = Column(Text)

    #: Description of the location of the event
    location = Column(Text, nullable=True)

    #: Tags/Categories of the event
    _tags = Column(MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    @property
    def tags(self):
        """ Tags/Categories of the event. """

        return list(self._tags.keys()) if self._tags else []

    @tags.setter
    def tags(self, value):
        self._tags = dict(((key.strip(), '') for key in value))

    #: Timezone of the event
    timezone = Column(String, nullable=False)

    #: Start date and time of the event (of the first event if recurring)
    start = Column(UTCDateTime, nullable=False)

    @property
    def localized_start(self):
        """ The localized version of the start date/time. """

        return to_timezone(self.start, self.timezone)

    #: End date and time of the event (of the first event if recurring)
    end = Column(UTCDateTime, nullable=False)

    @property
    def localized_end(self):
        """ The localized version of the end date/time. """

        return to_timezone(self.end, self.timezone)

    def as_ical(self, description=None, rrule=None, url=None):
        """ Returns the occurrence as iCalendar string. """

        event = icalendar.Event()
        event.add('summary', self.title)
        event.add('dtstart', to_timezone(self.start, UTC))
        event.add('dtend', to_timezone(self.end, UTC))
        event.add('last-modified',
                  self.modified or self.created or datetime.utcnow())
        event['location'] = icalendar.vText(self.location)
        if description:
            event['description'] = icalendar.vText(description)
        if rrule:
            event['rrule'] = icalendar.vRecur(
                icalendar.vRecur.from_ical(rrule.replace('RRULE:', ''))
            )
        if url:
            event.add('url', url)

        cal = icalendar.Calendar()
        cal.add('prodid', '-//OneGov//onegov.event//')
        cal.add('version', '2.0')
        cal.add_component(event)

        return cal.to_ical()
