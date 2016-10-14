import morepath
import re


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
