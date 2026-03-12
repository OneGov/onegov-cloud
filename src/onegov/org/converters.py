from __future__ import annotations

import morepath

from collections import defaultdict


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Protocol

    class HasKeywords(Protocol):
        @property
        def keywords(self) -> Mapping[str, Sequence[str]]: ...


def keywords_encode(
    keywords: HasKeywords | Mapping[str, Sequence[str]]
) -> str:
    """ Takes a dictionary of keywords and encodes them into a somewhat
    readable url query format.

    For example::

        {
            'color': ['blue', 'red'],
            'weight': ['normal']
        }

    Results in::

        '+color:blue+color:red+weight:normal'

    Instead of a dictionary we can also use any kind of object
    which has a 'keywords' property returning the expected dictionary.

    Note that that object won't be recreated during decode however.

    """

    if not keywords:
        return ''

    if hasattr(keywords, 'keywords'):
        keywords = keywords.keywords

    def escape(s: str) -> str:
        return s.replace('+', '++')

    return '+'.join(
        '{}:{}'.format(escape(key), escape(value))
        for key in keywords for value in keywords[key]
    )


def keywords_decode(text: str) -> dict[str, list[str]] | None:
    """ Decodes keywords creaged by :func:`keywords_encode`. """

    if not text:
        return None

    result = defaultdict(list)

    for item in text.replace('++', '\0').split('+'):
        key, value = item.split(':', 1)
        result[key.replace('\0', '+')].append(value.replace('\0', '+'))

    return result


keywords_converter = morepath.Converter(
    decode=keywords_decode,
    encode=keywords_encode  # type:ignore[arg-type]
)
