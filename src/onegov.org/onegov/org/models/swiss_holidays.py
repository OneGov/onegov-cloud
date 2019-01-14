from collections import defaultdict
from datetime import date, datetime
from dateutil.easter import easter
from dateutil.relativedelta import MO, TH, FR
from dateutil.relativedelta import relativedelta as rd
from onegov.org import _


CANTONS = {
    'AG': _('Aargau'),
    'AR': _('Appenzell Ausserrhoden'),
    'AI': _('Appenzell Innerrhoden'),
    'BL': _('Basel-Landschaft'),
    'BS': _('Basel-Stadt'),
    'BE': _('Berne'),
    'FR': _('Fribourg'),
    'GE': _('Geneva'),
    'GL': _('Glarus'),
    'GR': _('Grisons'),
    'JU': _('Jura'),
    'LU': _('Lucerne'),
    'NE': _('Neuchâtel'),
    'NW': _('Nidwalden'),
    'OW': _('Obwalden'),
    'SH': _('Schaffhausen'),
    'SZ': _('Schwyz'),
    'SO': _('Solothurn'),
    'SG': _('St. Gallen'),
    'TG': _('Thurgau'),
    'TI': _('Ticino'),
    'UR': _('Uri'),
    'VS': _('Valais'),
    'VD': _('Vaud'),
    'ZG': _('Zug'),
    'ZH': _('Zürich'),
}


class SwissHolidays(object):
    """ Provides the ability to check dates against Swiss holidays and to
    list the holidays for a given year. Builds on the code from
    python-holidays.

    See the ``Switzerland`` class here:
    https://github.com/dr-prodigy/python-holidays/blob/master/holidays.py

    Supports the following features which are not provided by python-holidays:

    * Translatable strings.
    * The ability to combine cantons.
    * The ability to add extra holidays for specific days of any year.

    The interface is inspired by pyhton-holidays, thought he API surface
    is a bit smaller and there is less magic.

    """

    def __init__(self, cantons=(), other=(), timezone='Europe/Zurich'):
        self._cantons = set()
        self._other = defaultdict(set)

        for canton in cantons:
            self.add_canton(canton)

        for month, day, description in other:
            self.add_holiday(month, day, description)

    def add_canton(self, canton):
        assert canton in CANTONS

        self._cantons.add(canton)

    def add_holiday(self, month, day, description):
        assert 1 <= month <= 12
        assert 1 <= day <= 31

        self._other[(month, day)].add(description)

    def __bool__(self):
        return (self._cantons or self._other) and True or False

    def __contains__(self, dt):
        if not isinstance(dt, date) or isinstance(dt, datetime):
            raise ValueError(f"Unsupported type: {type(dt)}")

        if (dt.month, dt.day) in self._other:
            return True

        for holiday, descriptions in self.official(dt.year):
            if holiday == dt:
                return True

        return False

    def all(self, year):
        """ Returns all the holidays for the given year for the current
        set of cantons. If no cantons are selected and no other holidays
        are defined, nothing is returned.

        The result is a list in chronological order with each list entry
        being at tuple of date and at least one description (if multiple
        holidays are on a single day, a list of descriptions is returned).

        The list of descriptions is sorted alphabetically.

        """

        combined = defaultdict(set)

        for dt, descriptions in self.official(year):
            combined[dt].update(descriptions)

        for month, day in self._other:
            combined[date(year, month, day)] |= self._other[(month, day)]

        dates = sorted(list(combined.keys()))

        return [(dt, sorted(combined[dt])) for dt in dates]

    def between(self, start, end):
        """ Returns all the holidays between the given start and end date in
        the same manner ass :meth:`all`.

        """
        assert start <= end

        if start.year == end.year:
            years = (start.year, )
        else:
            years = (start.year, end.year)

        def generate():
            for year in years:
                for dt, descriptions in self.all(year):
                    if start <= dt and dt <= end:
                        yield dt, descriptions

        return list(generate())

    def other(self, year):
        """ Returns all custom defined holidays for the given year. """

        for month, day in self._other:
            yield date(year, month, day), self._other[(month, day)]

    def official(self, year):
        """ Like :meth:`all`, but only includes the official holidays,
        not the custom defined ones.

        If no cantons are selected, no official holidays are returned, not
        even the national ones.

        The description only ever contains a tuple with one item. This is
        for congruence with the other methods of this class, where the
        description is always in an iterable (not necessarily a tuple).

        """

        if not self._cantons:
            return

        yield date(year, 1, 1), (_("Neujahrestag"), )

        if self._cantons & {'AG', 'BE', 'FR', 'GE', 'GL', 'GR', 'JU', 'LU',
                            'NE', 'OW', 'SH', 'SO', 'TG', 'VD', 'ZG', 'ZH'}:

            yield date(year, 1, 2), (_("Berchtoldstag"), )

        if self._cantons & {'SZ', 'TI', 'UR'}:
            yield date(year, 1, 6), (_("Heilige Drei Könige"), )

        if self._cantons & {'NE'}:
            yield date(year, 3, 1), (
                _("Jahrestag der Ausrufung der Republik"), )

        if self._cantons & {'NW', 'SZ', 'TI', 'UR', 'VS'}:
            yield date(year, 3, 19), (_("Josefstag"), )

        if self._cantons & {'GL'} and year >= 1835:

            # First Thursday in April but not in Holy Week
            if date(year, 4, 1) + rd(weekday=FR) != easter(year) - rd(days=2):
                yield date(year, 4, 1) + rd(weekday=TH), (
                    _("Näfelser Fahrt"), )
            else:
                yield date(year, 4, 8) + rd(weekday=TH), (
                    _("Näfelser Fahrt"), )

        yield easter(year), (_("Ostern"), )

        # Good Friday is celebrated if we have a canton other than TI, VS
        if self._cantons > {'TI', 'VS'}:
            yield easter(year) - rd(days=2), (_("Karfreitag"), )

        # Easter Monday is celebrated if we have a canton other than VS
        if self._cantons > {'VS'}:
            yield easter(year) + rd(weekday=MO), (_("Ostermontag"), )

        if self._cantons & {
                'BL', 'BS', 'JU', 'NE', 'SH', 'SO', 'TG', 'TI', 'ZH'}:
            yield date(year, 5, 1), (_("Tag der Arbeit"), )

        yield easter(year) + rd(days=39), (_("Auffahrt"), )
        yield easter(year) + rd(days=49), (_("Pfingsten"), )
        yield easter(year) + rd(days=50), (_("Pfingstmontag"), )

        if self._cantons & {
                'AI', 'JU', 'LU', 'NW', 'OW', 'SZ', 'TI', 'UR', 'VS', 'ZG'}:
            yield easter(year) + rd(days=60), (_("Fronleichnam"), )

        if self._cantons & {'JU'}:
            yield date(year, 6, 23), (_("Fest der Unabhängigkeit"), )

        if self._cantons & {'TI'}:
            yield date(year, 6, 29), (_("Peter und Paul"), )

        if year >= 1994:
            yield date(year, 8, 1), (_("Nationalfeiertag"), )

        if self._cantons & {
                'AI', 'JU', 'LU', 'NW', 'OW', 'SZ', 'TI', 'UR', 'VS', 'ZG'}:
            yield date(year, 8, 15), (_("Mariä Himmelfahrt"), )

        if self._cantons & {'OW'}:
            yield date(year, 9, 25), (_("Bruder Klaus"), )

        if self._cantons & {
                'AI', 'GL', 'JU', 'LU', 'NW', 'OW', 'SG', 'SZ', 'TI', 'UR',
                'VS', 'ZG'}:
            yield date(year, 11, 1), (_("Allerheiligen"), )

        if self._cantons & {
                'AI', 'LU', 'NW', 'OW', 'SZ', 'TI', 'UR', 'VS', 'ZG'}:
            yield date(year, 12, 8), (_("Mariä Empfängnis"), )

        if self._cantons & {'GE'}:
            yield date(year, 12, 12), (_("Escalade de Genève"), )

        yield date(year, 12, 25), (_("Weihnachten"), )

        if self._cantons & {
                'AG', 'AR', 'AI', 'BL', 'BS', 'BE', 'FR', 'GL', 'GR', 'LU',
                'NE', 'NW', 'OW', 'SG', 'SH', 'SZ', 'SO', 'TG', 'TI', 'UR',
                'ZG', 'ZH'}:
            yield date(year, 12, 26), (_("Stephanstag"), )

        if self._cantons & {'GE'}:
            yield date(year, 12, 31), (_("Wiederherstellung der Republik"), )
