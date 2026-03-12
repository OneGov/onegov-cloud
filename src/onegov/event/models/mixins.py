from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import ContentMixin
from sedate import to_timezone
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable


class OccurrenceMixin(ContentMixin):
    """ Contains all attributes events and ocurrences share.

    The ``start`` and ``end`` date and times are stored in UTC - that is, they
    are stored internally without a timezone and are converted to UTC when
    getting or setting, see :class:`UTCDateTime`. Use the properties
    ``localized_start`` and ``localized_end`` to get the localized version of
    the date and times.
    """

    #: Title of the event
    title: Mapped[str]

    #: A nice id for the url, readable by humans
    name: Mapped[str | None]

    #: Description of the location of the event
    location: Mapped[str | None]

    #: Tags/Categories of the event
    _tags: Mapped[dict[str, str] | None] = mapped_column(
        MutableDict.as_mutable(HSTORE),
        name='tags'
    )

    @property
    def tags(self) -> list[str]:
        """ Tags/Categories of the event. """

        return list(self._tags.keys()) if self._tags else []

    @tags.setter
    def tags(self, value: Iterable[str]) -> None:
        self._tags = {key.strip(): '' for key in value}

    #: Filter keywords if organisation settings enabled filters
    filter_keywords: dict_property[dict[str, list[str] | str]] = (
        content_property(default=dict)
    )

    #: Timezone of the event
    timezone: Mapped[str] = mapped_column(String)

    #: Start date and time of the event (of the first event if recurring)
    start: Mapped[datetime]

    @property
    def localized_start(self) -> datetime:
        """ The localized version of the start date/time. """

        return to_timezone(self.start, self.timezone)

    #: End date and time of the event (of the first event if recurring)
    end: Mapped[datetime]

    @property
    def localized_end(self) -> datetime:
        """ The localized version of the end date/time. """

        return to_timezone(self.end, self.timezone)

    def filter_keywords_ordered(
            self,
    ) -> dict[str, list[str] | str | None]:
        return OrderedDict((k, sorted(v) if isinstance(v, list) else v)
                           for k, v in sorted(self.filter_keywords.items()))
