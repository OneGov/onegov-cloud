import morepath
import re

from datetime import date


AGE_RANGE_RE = re.compile(r'[0-9]+-[0-9]+')


def age_range_decode(s):
    if not isinstance(s, str):
        return None

    if not AGE_RANGE_RE.match(s):
        return None

    age_range = tuple(int(a) for a in s.split('-'))

    if age_range[0] < age_range[1]:
        return age_range
    else:
        return None


def age_range_encode(a):
    return '-'.join(str(n) for n in a)


age_range_converter = morepath.Converter(
    decode=age_range_decode, encode=age_range_encode
)


DATE_RANGE_RE = re.compile(
    r'[0-9]{4}-[0-9]{2}-[0-9]{2}:[0-9]{4}-[0-9]{2}-[0-9]{2}'
)


def date_range_decode(s):
    if not isinstance(s, str):
        return None

    if not DATE_RANGE_RE.match(s):
        return None

    s, e = s.split(':')

    return (
        date(*tuple(int(p) for p in s.split('-'))),
        date(*tuple(int(p) for p in e.split('-')))
    )


def date_range_encode(d):
    return ':'.join((d[0].strftime('%Y-%m-%d'), d[1].strftime('%Y-%m-%d')))


date_range_converter = morepath.Converter(
    decode=date_range_decode, encode=date_range_encode
)
