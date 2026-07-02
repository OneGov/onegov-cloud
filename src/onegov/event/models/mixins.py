from __future__ import annotations

from datetime import datetime
from onegov.core.orm.mixins import ContentMixin
from sedate import to_timezone
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from webob.multidict import MultiDict


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from sqlalchemy.ext.associationproxy import AssociationProxy


def proxied_multidict(items: list[tuple[str, str]]) -> MultiDict[str, str]:
    # NOTE: MultiDict.view_list asserts that a list instance is used but
    #       AssociationProxy provides its own duck-typed list class, so
    #       we need to manually bypass this check
    result: MultiDict[str, str] = MultiDict()
    result._items = items  # type: ignore[attr-defined]
    return result


class OccurrenceMixin(ContentMixin):
    """ Contains all attributes events and ocurrences share.

    The ``start`` and ``end`` date and times are stored in UTC - that is, they
    are stored internally without a timezone and are converted to UTC when
    getting or setting, see :class:`UTCDateTime`. Use the properties
    ``localized_start`` and ``localized_end`` to get the localized version of
    the date and times.
    """

    if TYPE_CHECKING:
        # forward declare required attributes
        filter_keyword_list: AssociationProxy[list[tuple[str, str]]]

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
    @property
    def filter_keywords(self) -> MultiDict[str, str]:
        assert self.filter_keyword_list is not None
        return proxied_multidict(self.filter_keyword_list)

    @filter_keywords.setter
    def filter_keywords(
        self,
        value: Mapping[str, str | list[str]] | None
    ) -> None:
        if not value:
            self.filter_keyword_list.clear()
            return

        self.filter_keyword_list = [
            (key, value)
            for key, values in value.items()
            for value in (values if isinstance(values, list) else [values])
        ]

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

    def filter_keywords_ordered(self) -> dict[str, list[str]]:
        return MultiDict.view_list(
            sorted(self.filter_keyword_list)
        ).dict_of_lists()
