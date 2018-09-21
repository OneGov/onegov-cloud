import morepath

from collections import defaultdict


def keywords_encode(d):
    """ Takes a dictionary of keywords and encodes them into a somewhat
    readable url query format.

    For example:

        {
            'color': ['blue', 'red'],
            'weight': ['normal']
        }

    Results in

        '+color:blue+color:red+weight:normal'

    Instead of a dictionary we can also use any kind of object
    which has a 'keywords' property returning the expected dictionary.

    Note that that object won't be recreated during decode however.

    """

    if not d:
        return ''

    if hasattr(d, 'keywords'):
        d = d.keywords

    return '+'.join('{}:{}'.format(k, v) for k in d for v in d[k])


def keywords_decode(s):
    """ Deocdes keywords creaged by :func:`keywords_encode`. """

    if not s:
        return None

    result = defaultdict(list)

    for item in s.split('+'):
        key, value = item.split(':', 1)
        result[key].append(value)

    return result


keywords_converter = morepath.Converter(
    decode=keywords_decode, encode=keywords_encode
)
