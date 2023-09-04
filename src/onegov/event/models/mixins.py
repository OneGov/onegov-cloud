from onegov.core.orm.types import UTCDateTime
from sedate import to_timezone
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict


class OccurrenceMixin:
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
    _tags = Column(  # type:ignore[call-overload]
        MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    #: All filter keywords defined for this entry
    _filter_keywords = Column(  # type:ignore
        MutableDict.as_mutable(HSTORE), nullable=True, name='filter_keywords'
    )

    @property
    def tags(self):
        """ Tags/Categories of the event. """

        return list(self._tags.keys()) if self._tags else []

    @tags.setter
    def tags(self, value):
        self._tags = dict(((key.strip(), '') for key in value))

    @property
    def filter_keywords(self):
        return set(self._filter_keywords.keys()) if self._filter_keywords \
            else set()

    @filter_keywords.setter
    def filter_keywords(self, value):
        self._filter_keywords = {k: '' for k in value} if value else None

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
