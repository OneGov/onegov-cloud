from __future__ import annotations

from collections import OrderedDict

from onegov.core.orm.mixins import content_property, ContentMixin
from onegov.core.orm.types import UTCDateTime
from sedate import to_timezone
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from onegov.core.orm.mixins import dict_property


class OccurrenceMixin(ContentMixin):
    """ Contains all attributes events and ocurrences share.

    The ``start`` and ``end`` date and times are stored in UTC - that is, they
    are stored internally without a timezone and are converted to UTC when
    getting or setting, see :class:`UTCDateTime`. Use the properties
    ``localized_start`` and ``localized_end`` to get the localized version of
    the date and times.
    """

    #: Title of the event
    title: Column[str] = Column(Text, nullable=False)

    #: A nice id for the url, readable by humans
    name: Column[str | None] = Column(Text)

    #: Description of the location of the event
    location: Column[str | None] = Column(Text, nullable=True)

    #: Tags/Categories of the event
    _tags: Column[dict[str, str] | None] = Column(  # type:ignore
        MutableDict.as_mutable(HSTORE),  # type:ignore[no-untyped-call]
        nullable=True,
        name='tags'
    )

    @property
    def tags(self) -> list[str]:
        """ Tags/Categories of the event. """

        return list(self._tags.keys()) if self._tags else []

    # FIXME: asymmetric properties are not supported, if we need to
    #        be able to set this with arbitrary iterables we need
    #        to define a custom descriptor
    @tags.setter
    def tags(self, value: Iterable[str]) -> None:
        self._tags = {key.strip(): '' for key in value}

    #: Filter keywords if organisation settings enabled filters
    filter_keywords: dict_property[dict[str, list[str] | str]] = (
        content_property(default=dict)
    )

    #: Timezone of the event
    timezone: Column[str] = Column(String, nullable=False)

    #: Start date and time of the event (of the first event if recurring)
    start: Column[datetime] = Column(UTCDateTime, nullable=False)

    @property
    def localized_start(self) -> datetime:
        """ The localized version of the start date/time. """

        return to_timezone(self.start, self.timezone)

    #: End date and time of the event (of the first event if recurring)
    end: Column[datetime] = Column(UTCDateTime, nullable=False)

    @property
    def localized_end(self) -> datetime:
        """ The localized version of the end date/time. """

        return to_timezone(self.end, self.timezone)

    def filter_keywords_ordered(
            self,
    ) -> dict[str, list[str] | str | None]:
        return OrderedDict((k, sorted(v) if isinstance(v, list) else v)
                           for k, v in sorted(self.filter_keywords.items()))
