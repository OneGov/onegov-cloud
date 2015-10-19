import arrow
import babel.dates
import babel.numbers
import numbers

from cached_property import cached_property
from datetime import datetime
from itertools import zip_longest
from purl import URL
from pytz import timezone


class Layout(object):
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
    #: http://www.unicode.org\
    #:       /reports/tr35/tr35-39/tr35-dates.html#Date_Format_Patterns
    #:
    #: Classes inheriting from :class:`Layout` may add their own formats, as
    #: long as they end in ``_format``. For example::
    #:
    #:    class MyLayout(Layout):
    #:        my_format = 'dd.MMMM'
    #:
    #:    MyLayout().format_date(dt, 'my')
    #:
    #: XXX this is not yet i18n and could be done better
    time_format = 'HH:mm'
    date_format = 'dd.MM.YYYY'
    datetime_format = 'dd.MM.YYYY HH:mm'

    date_long_format = 'dd. MMMM YYYY'
    datetime_long_format = 'd. MMMM YYYY HH:mm'
    weekday_long_format = 'EEEE'
    month_long_format = 'MMMM'

    def __init__(self, model, request):
        self.model = model
        self.request = request

    @cached_property
    def app(self):
        """ Returns the application behind the request. """
        return self.request.app

    def chunks(self, iterable, n, fillvalue=None):
        """ Iterates through an iterable, returning chunks with the given size.

        For example::

            chunks('ABCDEFG', 3, 'x') --> [
                ('A', 'B', 'C'),
                ('D', 'E', 'F'),
                ('G', 'x', 'x')
            ]

        """

        args = [iter(iterable)] * n
        return zip_longest(fillvalue=fillvalue, *args)

    @cached_property
    def csrf_token(self):
        """ Returns a csrf token for use with DELETE links (forms do their
        own thing automatically).

        """
        return self.request.new_csrf_token()

    def csrf_protected_url(self, url):
        """ Adds a csrf token to the given url. """
        return URL(url).query_param('csrf-token', self.csrf_token).as_string()

    def format_date(self, dt, format):
        """ Takes a datetime and formats it according to local timezone and
        the given format.

        """
        if getattr(dt, 'tzinfo', None) is not None:
            dt = self.timezone.normalize(dt.astimezone(self.timezone))

        if format == 'relative':
            dt = arrow.get(dt)

            try:
                return dt.humanize(locale=self.request.locale)
            except ValueError:
                return dt.humanize(locale=self.request.locale.split('_')[0])

        if hasattr(dt, 'hour'):
            formatter = babel.dates.format_datetime
        else:
            formatter = babel.dates.format_date

        return formatter(
            dt,
            format=getattr(self, format + '_format'),
            locale=self.request.locale
        )

    def isodate(self, date):
        """ Returns the given date in the ISO 8601 format. """
        return datetime.isoformat(date)

    def format_number(self, number, decimal_places=None):
        """ Takes the given numer and formats it according to locale.

        If the number is an integer, the default decimal places are 0,
        otherwise 2.

        """
        if decimal_places is None:
            if isinstance(number, numbers.Integral):
                decimal_places = 0
            else:
                decimal_places = 2

        locale = self.request.locale

        decimal = babel.numbers.get_decimal_symbol(locale)
        group = babel.numbers.get_group_symbol(locale)

        result = '{{:,.{}f}}'.format(decimal_places).format(number)
        return result.translate({ord(','): group, ord('.'): decimal})


class ChameleonLayout(Layout):
    """ Extends the base layout class with methods related to chameleon
    template rendering.

    This class assumes the existance of two templates:

    - layout.pt -> Contains the page skeleton with headers, body and so on.
    - macros.pt -> Contains chameleon macros.

    """

    @cached_property
    def template_loader(self):
        """ Returns the chameleon template loader. """
        return self.app.registry._template_loaders['.pt']

    @cached_property
    def base(self):
        """ Returns the layout, which defines the base layout of all town
        pages. See ``templates/layout.pt``.

        """
        return self.template_loader['layout.pt']

    @cached_property
    def macros(self):
        """ Returns the macros, which offer often used html constructs.
        See ``templates/macros.pt``.

        """
        return self.template_loader['macros.pt']
