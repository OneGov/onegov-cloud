from collections import OrderedDict

from onegov.core.orm.mixins import content_property, ContentMixin
from onegov.core.orm.types import UTCDateTime
from sedate import to_timezone
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict


class OccurrenceMixin(ContentMixin):
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

    @property
    def tags(self):
        """ Tags/Categories of the event. """

        return list(self._tags.keys()) if self._tags else []

    @tags.setter
    def tags(self, value):
        self._tags = {key.strip(): '' for key in value}

    #: Filter keywords if organisation settings enabled filters
    filter_keywords = content_property(value_type=dict)

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

    def filter_keywords_ordered(self, order=None):
        order = order or []
        if order:
            return OrderedDict((k, self.filter_keywords.get(k)) for k in order)

        return OrderedDict(sorted(self.filter_keywords.items()))
