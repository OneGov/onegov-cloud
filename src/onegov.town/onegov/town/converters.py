""" Contains custom converters used by onegov.town. """

import morepath
from datetime import date
from time import mktime, strptime


def extended_date_decode(s):
    """ Decodes a date string HTML5 (RFC3339) compliant."""
    if not s:
        return None

    return date.fromtimestamp(mktime(strptime(s, '%Y-%m-%d')))


def extended_date_encode(d):
    """ Encodes a date HTML5 (RFC3339) compliant. """
    if not d:
        return ''

    return d.strftime('%Y-%m-%d')


extended_date_converter = morepath.Converter(
    decode=extended_date_decode, encode=extended_date_encode
)
