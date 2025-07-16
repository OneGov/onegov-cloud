from __future__ import annotations


import isodate
import numbers
import sedate

from datetime import datetime
from functools import cached_property
from onegov.core import utils
from onegov.core.templates import PageTemplate
from pytz import timezone

from typing import overload, Any, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from chameleon import PageTemplateFile
    from collections.abc import Callable, Collection, Iterable, Iterator
    from datetime import date
    from decimal import Decimal

    from .framework import Framework
    from .request import CoreRequest
    from .templates import MacrosLookup, TemplateLoader

_T = TypeVar('_T')


class Layout:
    """ Contains useful methods related to rendering pages in html. Think of it
    as an API that you can rely on in your templates.

    The idea is to provide basic layout functions here, if they are usful for
    any kind of html application. You should then extend the core layout
    classes with your own.

    """

    #: The timezone is currently fixed to 'Europe/Zurich' since all our
    #: business with onegov is done here. Once the need arises, we should
    #: lookup the timezone from the IP of the user, or use a javascript
    #: library that sets the timezone for the user session.
    #:
    #: There's also going to be the case where we want the timezone set
    #: specifically for a certain layout (say a reservation of a room, where
    #: the room's timezone is relevant). This is why this setting should
    #: remain close to the layout, and not necessarily close to the request.
    timezone = timezone('Europe/Zurich')

    #: Just like the timezone, these values are fixed for Switzerland now,
    #: though the non-numerical information is actually translated.
    #: Format:
    #
    #: http://www.unicode.org/reports/tr35/tr35-39/tr35-dates.html
    #: #Date_Format_Patterns
    #: Skeleton Patterns:
    #
    #: http://cldr.unicode.org/translation/date-time-patterns
    #:
    #: Classes inheriting from :class:`Layout` may add their own formats, as
    #: long as they end in ``_format``. For example::
    #:
    #:     class MyLayout(Layout):
    #:         my_format = 'dd.MMMM'
    #:         my_skeleton_format = 'skeleton:yMMM'
    #:
    #:     MyLayout().format_date(dt, 'my')
    #:
    #: XXX this is not yet i18n and could be done better
    time_format = 'HH:mm'
    date_format = 'dd.MM.yyyy'
    datetime_format = 'dd.MM.yyyy HH:mm'

    date_long_format = 'dd. MMMM yyyy'
    datetime_long_format = 'd. MMMM yyyy HH:mm'
    weekday_long_format = 'EEEE'
    weekday_short_format = 'E'
    month_long_format = 'MMMM'

    custom_body_attributes: dict[str, Any]
    custom_html_attributes: dict[str, Any]

    def __init__(self, model: Any, request: CoreRequest):
        self.model = model
        self.request = request
        self.custom_body_attributes = {}
        self.custom_html_attributes = {
            'data-version': self.request.app.version
        }
        if request.app.sentry_dsn:
            self.custom_html_attributes[
                'data-sentry-dsn'
            ] = request.app.sentry_dsn

    @cached_property
    def app(self) -> Framework:
        """ Returns the application behind the request. """
        return self.request.app

    @overload
    def batched(
        self,
        iterable: Iterable[_T],
        batch_size: int,
        container_factory: type[tuple] = ...  # type:ignore[type-arg]
    ) -> Iterator[tuple[_T, ...]]: ...

    @overload
    def batched(
        self,
        iterable: Iterable[_T],
        batch_size: int,
        container_factory: type[list]  # type:ignore[type-arg]
    ) -> Iterator[list[_T]]: ...

    # NOTE: If there were higher order TypeVars, we could properly infer
    #       the type of the Container, for now we just add overloads for
    #       two of the most common container_factories
    @overload
    def batched(
        self,
        iterable: Iterable[_T],
        batch_size: int,
        container_factory: Callable[[Iterator[_T]], Collection[_T]]
    ) -> Iterator[Collection[_T]]: ...

    def batched(
        self,
        iterable: Iterable[_T],
        batch_size: int,
        container_factory: Callable[[Iterator[_T]], Collection[_T]] = tuple
    ) -> Iterator[Collection[_T]]:
        """ See :func:`onegov.core.utils.batched`. """

        return utils.batched(
            iterable,
            batch_size,
            container_factory
        )

    @property
    def csrf_token(self) -> str:
        """ Returns a csrf token for use with DELETE links (forms do their
        own thing automatically).

        """
        return self.request.csrf_token

    def csrf_protected_url(self, url: str) -> str:
        """ Adds a csrf token to the given url. """
        return self.request.csrf_protected_url(url)

    def format_date(self, dt: datetime | date | None, format: str) -> str:
        fmt = getattr(self, f'{format}_format', format)
        return self.request.format_date(dt, fmt)

    def isodate(self, date: datetime) -> str:
        """ Returns the given date in the ISO 8601 format. """
        return datetime.isoformat(date)

    def parse_isodate(self, string: str) -> datetime:
        """ Returns the given ISO 8601 string as datetime. """
        return isodate.parse_datetime(string)

    def format_number(
        self,
        number: numbers.Number | Decimal | float | str | None,
        decimal_places: int | None = None,
        padding: str = ''
    ) -> str:
        return self.request.format_number(number, decimal_places, padding)

    @property
    def view_name(self) -> str | None:
        """ Returns the view name of the current view, or None if it is the
        default view.

        Note: This relies on morepath internals and is experimental in nature!

        """
        return self.request.unconsumed and self.request.unconsumed[-1] or None

    def today(self) -> date:
        return self.now().date()

    def now(self) -> datetime:
        return sedate.to_timezone(sedate.utcnow(), self.timezone)


class ChameleonLayout(Layout):
    """ Extends the base layout class with methods related to chameleon
    template rendering.

    This class assumes the existance of two templates:

    - layout.pt -> Contains the page skeleton with headers, body and so on.
    - macros.pt -> Contains chameleon macros.

    """

    @cached_property
    def template_loader(self) -> TemplateLoader:
        """ Returns the chameleon template loader. """
        return self.request.template_loader

    @cached_property
    def base(self) -> PageTemplateFile:
        """ Returns the layout, which defines the base layout of all pages.

        See ``templates/layout.pt``.

        """
        return self.template_loader['layout.pt']

    @cached_property
    def macros(self) -> MacrosLookup:
        """ Returns the macros, which offer often used html constructs.
        See ``templates/macros.pt``.

        """
        return self.template_loader.macros

    @cached_property
    def elements(self) -> PageTemplate | PageTemplateFile:
        """ The templates used by the elements. Overwrite this with your
        own ``templates/elements.pt`` if neccessary.

        """
        try:
            return self.template_loader['elements.pt']
        except ValueError:
            return PageTemplate(
                """<xml xmlns="http://www.w3.org/1999/xhtml">
                    <metal:b define-macro="link">
                        <a tal:attributes="e.attrs">${e.text or ''}</a>
                    </metal:b>
                    <metal:b define-macro="img">
                        <img tal:attributes="e.attrs" />
                    </metal:b>
                </xml>"""
            )
