""" Sigh. Here we go again, *another* json implementation with support for:

- date
- datetime
- time

Because nobody else does all of these. And if they do (like standardjson), they
don't support decoding...

"""

import datetime
import isodate

from decimal import Decimal
from rapidjson import Encoder as RapidJsonEncoder
from rapidjson import Decoder as RapidJsonDecoder


class Encoder(RapidJsonEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return '__datetime__@' + isodate.datetime_isoformat(o)
        elif isinstance(o, datetime.date):
            return '__date__@' + isodate.date_isoformat(o)
        elif isinstance(o, Decimal):
            return '__decimal__@' + str(o)
        elif isinstance(o, datetime.time):
            return '__time__@' + isodate.time_isoformat(o)

        raise TypeError('{} is not JSON serializable'.format(repr(o)))


class Decoder(RapidJsonDecoder):
    def string(self, value):
        if value.startswith('__date__@'):
            return isodate.parse_date(value[9:])

        if value.startswith('__datetime__@'):
            return isodate.parse_datetime(value[13:])

        if value.startswith('__decimal__@'):
            return Decimal(value[12:])

        if value.startswith('__time__@'):
            return isodate.parse_time(value[9:])

        return value


def dumps(obj, *args, **kwargs):
    if obj is not None:
        return Encoder(*args, **kwargs)(obj)
    else:
        return None


def loads(value, *args, **kwargs):
    if value is not None:
        return Decoder(*args, **kwargs)(value)
    else:
        return {}


def dump(data, fp, *args, **kwargs):
    return fp.write(dumps(data, *args, **kwargs))


def load(fp, *args, **kwargs):
    return loads(fp.read(), *args, **kwargs)
