""" Contains custom converters used by onegov.town. """

import morepath

from datetime import date
from onegov.core.framework import Framework
from onegov.core.utils import is_uuid
from time import mktime, strptime
from uuid import UUID


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


def uuid_decode(s):
    """ Turns a uuid string into a UUID instance. """

    return is_uuid(s) and UUID(s) or None


def uuid_encode(uuid):
    """ Turns a UUID instance into a uuid string. """
    if not uuid:
        return ''

    if isinstance(uuid, str):
        return uuid

    return uuid.hex


uuid_converter = morepath.Converter(
    decode=uuid_decode, encode=uuid_encode
)


@Framework.converter(type=UUID)
def get_default_uuid_converter():
    return uuid_converter
