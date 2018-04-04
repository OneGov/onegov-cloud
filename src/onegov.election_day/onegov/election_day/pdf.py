from babel.dates import format_date
from babel.dates import format_time
from copy import deepcopy
from onegov.election_day import _
from onegov.pdf import Pdf as PdfBase


class Pdf(PdfBase):
    """ Our custom PDF class.

    This adds some custom styles, two tables (factoids, tables) and the ability
    to translate texts.
    """

    def __init__(self, *args, **kwargs):
        locale = kwargs.pop('locale', None)
        translations = kwargs.pop('translations', None)
        super(Pdf, self).__init__(*args, **kwargs)
        self.locale = locale
        self.translations = translations

    def adjust_style(self, font_size=10):
        """ Adds styles for votes and elections. """

        super(Pdf, self).adjust_style(font_size)

        self.style.indent_0 = deepcopy(self.style.normal)
        self.style.indent_1 = deepcopy(self.style.normal)
        self.style.indent_2 = deepcopy(self.style.normal)
        self.style.indent_0.leftIndent = 0 * self.style.indent_0.fontSize
        self.style.indent_1.leftIndent = 1 * self.style.indent_1.fontSize
        self.style.indent_2.leftIndent = 2 * self.style.indent_2.fontSize

        self.style.table_results_1 = self.style.tableHead + (
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        )
        self.style.table_results_2 = self.style.tableHead + (
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        )
        self.style.table_results_3 = self.style.tableHead + (
            ('ALIGN', (0, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        )
        self.style.table_factoids = self.style.table + (
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
        )
        self.style.table_dates = self.style.table + (
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
        )

    def translate(self, text):
        """ Translates the given string. """

        if not hasattr(text, 'interpolate'):
            return text
        translator = self.translations.get(self.locale)
        return text.interpolate(translator.gettext(text))

    def h1(self, title):
        """ Translated H1. """

        super(Pdf, self).h1(self.translate(title))

    def h2(self, title):
        """ Translated H2. """

        super(Pdf, self).h2(self.translate(title))

    def h3(self, title):
        """ Translated H3. """

        super(Pdf, self).h3(self.translate(title))

    def figcaption(self, text):
        """ Translated Figcaption. """

        super(Pdf, self).figcaption(self.translate(text))

    def dates_line(self, date, changed):
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

    def factoids(self, headers, values):
        """ Adds a table with factoids. """

        assert len(headers) and len(headers) == len(values)
        self.table(
            [[self.translate(header) for header in headers], values],
            'even',
            style=self.style.table_factoids
        )

    def results(self, headers, values, spacing, style):
        """ Adds a table with results. """

        self.table(
            [[self.translate(header) for header in headers]] + values,
            spacing,
            style=style
        )
