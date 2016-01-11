from arrow import locales
from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp


@ElectionDayApp.view(model=SiteLocale, permission=Public)
def change_site_locale(self, request):
    return self.redirect()


# hack support for romansh into arrow, until we can get a proper translation
# (this one is not verified). Once we have that, we open a pull request.
if 'rm' not in locales._locales:
    class RomanshLocale(locales.Locale):

        names = ['rm', 'rm_ch']

        past = 'avant {0}'
        future = 'en {0}'

        timeframes = {
            'now': 'en quest mument',
            'seconds': 'secundas',
            'minute': 'ina minuta',
            'minutes': '{0} minutas',
            'hour': 'in\'ura',
            'hours': '{0} ura',
            'day': 'in di',
            'days': '{0} dis',
            'month': 'in mais',
            'months': '{0} mais',
            'year': 'in onn',
            'years': '{0} onns',
        }

        month_names = [
            '', 'schaner', 'favrer', 'mars', 'avrigl', 'matg', 'zercladur',
            'fanadur', 'avust', 'settember', 'october', 'november', 'december'
        ]

        month_abbreviations = [
            '', 'schan', 'fav', 'mars', 'avr', 'matg', 'zer', 'fan', 'avu',
            'set', 'oct', 'nov', 'dec'
        ]

        day_names = [
            '', 'glindesdi', 'mardi', 'mesemna', 'gievgia', 'venderdi',
            'sonda', 'dumengia'
        ]

        day_abbreviations = [
            '', 'gli', 'ma', 'me', 'gie', 've', 'so', 'du'
        ]

        def _ordinal_number(self, n):
            return '{0}.'.format(n)

    locales._locales['rm'] = RomanshLocale
    locales._locales['rm_ch'] = RomanshLocale
