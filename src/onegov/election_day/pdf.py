from __future__ import annotations

from babel.dates import format_date
from babel.dates import format_time
from copy import deepcopy
from onegov.election_day import _
from onegov.pdf import Pdf as PdfBase


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from datetime import datetime
    from gettext import GNUTranslations
    from reportlab.lib.styles import PropertySet


class Pdf(PdfBase):
    """ Our custom PDF class.

    This adds some custom styles, two tables (factoids, tables) and the ability
    to translate texts.
    """
    def __init__(
        self,
        *args: Any,
        locale: str | None = None,
        translations: dict[str, GNUTranslations] | None = None,
        toc_levels: int = 3,
        created: str = '',
        logo: str | None = None,
        link_color: str | None = None,
        underline_links: bool = False,
        underline_width: float | str = 0.5,
        **kwargs: Any
    ):

        super().__init__(
            *args,
            toc_levels=toc_levels,
            created=created,
            logo=logo,
            link_color=link_color,
            underline_links=underline_links,
            underline_width=underline_width,
            **kwargs
        )
        self.locale = locale
        self.translations = translations or {}

    def adjust_style(self, font_size: int = 10) -> None:
        """ Adds styles for votes and elections. """

        super().adjust_style(font_size)

        self.style.indent_0 = deepcopy(self.style.normal)
        self.style.indent_1 = deepcopy(self.style.normal)
        self.style.indent_2 = deepcopy(self.style.normal)
        self.style.indent_0.leftIndent = 0 * self.style.indent_0.fontSize
        self.style.indent_1.leftIndent = 1 * self.style.indent_1.fontSize
        self.style.indent_2.leftIndent = 2 * self.style.indent_2.fontSize

        self.style.table_results = (
            *self.style.tableHead,
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        )
        self.style.table_factoids = (
            *self.style.table,
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
        )
        self.style.table_dates = (
            *self.style.table,
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
        )

    def translate(self, text: str) -> str:
        """ Translates the given string. """

        if not hasattr(text, 'interpolate'):
            return text

        translated = None
        if self.locale is not None:
            translator = self.translations.get(self.locale)
            if translator is not None:
                translated = translator.gettext(text)
        return text.interpolate(translated)

    def h1(self, title: str, style: PropertySet | None = None) -> None:
        """ Translated H1. """

        super().h1(self.translate(title), style=style)

    def h2(self, title: str, style: PropertySet | None = None) -> None:
        """ Translated H2. """

        super().h2(self.translate(title), style=style)

    def h3(self, title: str, style: PropertySet | None = None) -> None:
        """ Translated H3. """

        super().h3(self.translate(title), style=style)

    def figcaption(
        self,
        text: str,
        style: PropertySet | None = None
    ) -> None:
        """ Translated Figcaption. """

        super().figcaption(self.translate(text), style=style)

    def dates_line(self, date: date, changed: datetime | None) -> None:
        """ Adds the given date and timespamp. """

        self.table(
            [[
                format_date(date, format='long', locale=self.locale),
                '{}: {} {}'.format(
                    self.translate(_('Last change')),
                    format_date(changed, format='long', locale=self.locale),
                    format_time(changed, format='short', locale=self.locale)

                )
            ]],
            'even',
            style=self.style.table_dates
        )

    def factoids(self, headers: list[str], values: list[str]) -> None:
        """ Adds a table with factoids. """

        assert len(headers) and len(headers) == len(values)
        self.table(
            [[self.translate(header) for header in headers], values],
            'even',
            style=self.style.table_factoids
        )

    def results(
        self,
        head: list[str],
        body: list[list[Any]],
        foot: list[Any] | None = None,
        hide: list[bool] | None = None
    ) -> None:
        """ Adds a table with results. """

        assert not body or {len(column) for column in body} == {len(head)}
        assert not foot or len(foot) == len(head)
        assert not hide or len(hide) == len(head)

        columns = [[self.translate(cell) for cell in head], *body]
        if foot:
            columns += [foot]
        columns = [
            [
                str(cell) for index, cell in enumerate(column)
                if hide is None or not hide[index]
            ]
            for column in columns
        ]

        spacing = [None for index in enumerate(head)]

        self.table(columns, spacing, style=self.style.table_results)
