""" Sigh. Here we go again, *another* json implementation with support for:

- date
- datetime
- time

Because nobody else does all of these. And if they do (like standardjson), they
don't support decoding...

"""

import datetime
import isodate
import json

from onegov.core import compat
from onegov.core import utils


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return '__datetime__@' + isodate.datetime_isoformat(o)
        elif isinstance(o, datetime.date):
            return '__date__@' + isodate.date_isoformat(o)
        elif isinstance(o, datetime.time):
            return '__time__@' + isodate.time_isoformat(o)
        else:
            if isinstance(o, compat.string_types):
                # make sure the reserved words can't be added as a string by
                # some smartass that wants to screw with us
                o = utils.lchop(o, '__datetime__@')
                o = utils.lchop(o, '__date__@')
                o = utils.lchop(o, '__time__@')
            return super(CustomJSONEncoder, self).default(o)


def custom_json_decoder(value):
    if not isinstance(value, compat.string_types):
        return value

    if value.startswith(u'__date__@'):
        return isodate.parse_date(value[9:])

    if value.startswith(u'__datetime__@'):
        return isodate.parse_datetime(value[13:])

    if value.startswith(u'__time__@'):
        return isodate.parse_time(value[9:])

    return value


def json_loads_object_hook(dictionary):
    for key, value in dictionary.items():

        if isinstance(value, compat.string_types):
            dictionary[key] = custom_json_decoder(value)

        elif isinstance(value, (list, tuple)):
            dictionary[key] = map(custom_json_decoder, value)

    return dictionary


def encode_decimal(o):
    """ Encodes a Python decimal.Decimal object as an ECMA-262 compliant
    decimal string."""
    return str(o)


def dumps(obj):
    if obj is not None:
        return json.dumps(obj, cls=CustomJSONEncoder)
    else:
        return ''


def loads(value):
    if value is not None:
        return json.loads(value, object_hook=json_loads_object_hook)
    else:
        return {}
