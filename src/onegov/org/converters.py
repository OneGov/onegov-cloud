import morepath

from collections import defaultdict


def keywords_encode(keywords):
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

    if not keywords:
        return ''

    if hasattr(keywords, 'keywords'):
        keywords = keywords.keywords

    def escape(s):
        return s.replace('+', '++')

    return '+'.join(
        '{}:{}'.format(escape(key), escape(value))
        for key in keywords for value in keywords[key]
    )


def keywords_decode(text):
    """ Decodes keywords creaged by :func:`keywords_encode`. """

    if not text:
        return None

    result = defaultdict(list)

    for item in text.replace('++', '\0').split('+'):
        key, value = item.split(':', 1)
        result[key.replace('\0', '+')].append(value.replace('\0', '+'))

    return result


keywords_converter = morepath.Converter(
    decode=keywords_decode, encode=keywords_encode
)
