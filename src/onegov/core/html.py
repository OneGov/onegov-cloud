from __future__ import annotations

import re

from bleach.sanitizer import Cleaner
from html2text import HTML2Text
from markupsafe import Markup


from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable


_StrT = TypeVar('_StrT', bound=str)


# html tags allowed by bleach
SANE_HTML_TAGS = [
    'a',
    'abbr',
    'b',
    'br',
    'blockquote',
    'code',
    'del',
    'div',
    'em',
    'i',
    'img',
    'hr',
    'li',
    'ol',
    'p',
    'pre',
    'strong',
    'sup',
    'span',
    'ul',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'table',
    'tbody',
    'thead',
    'tr',
    'th',
    'td',
]

# html attributes allowed by bleach
SANE_HTML_ATTRS = {
    'a': ['href', 'title'],
    'abbr': ['title', ],
    'acronym': ['title', ],
    'img': ['src', 'alt', 'title'],
    'p': ['class']
}

# lines without these plaintext characters are excluded in html_to_text
VALID_PLAINTEXT_CHARACTERS = re.compile(r"""
    [
        \d  # decimals
        \w  # words
        \n  # new lines

        # emojis
        \U00002600-\U000027BF
        \U0001f300-\U0001f64F
        \U0001f680-\U0001f6FF
    ]+
""", re.VERBOSE)

# match empty link expressions
EMPTY_LINK = re.compile(r'\[\]\([^)]+\)')


cleaner = Cleaner(
    tags=SANE_HTML_TAGS,
    attributes=SANE_HTML_ATTRS
)


def sanitize_html(html: str | None) -> Markup:
    """ Takes the given html and strips all but a whitelisted number of tags
    from it.

    """

    return Markup(cleaner.clean(html or ''))  # nosec: B704


def sanitize_svg(svg: _StrT) -> _StrT:
    """ I couldn't find a good svg sanitiser function yet, so for now
    this function will be a no-op, though it will try to detect
    svg files which are harmful.

    I tried to go with bleach/html5lib, but the lack of xml namespace support
    makes those options a no go.

    In the future we want a proper SVG sanitiser here!

    """

    assert 'javascript:' not in svg
    assert 'CDATA' not in svg
    assert Markup('<script>') not in svg
    assert 'Set-Cookie' not in svg

    return svg


def html_to_text(
    html: str,
    *,
    unicode_snob: bool = True,
    body_width: int = 0,
    ignore_images: bool = True,
    single_line_break: bool = True,
    # FIXME: We may want to specify the other valid options
    **config: Any
) -> str:
    """ Takes the given HTML text and extracts the text from it.

    The result is markdown. The driver behind it is html2text. Have a look
    at https://github.com/Alir3z4/html2text/blob/master/html2text/__init__.py
    to see all options.

    """

    # filter out duplicated lines and lines without any text
    html2text = HTML2Text()

    # output unicode directly, instead of approximating it to ASCII
    html2text.unicode_snob = unicode_snob

    # do not wrap lines after a certain length
    html2text.body_width = body_width

    # images are just converted into somewhat useless links, so disable
    html2text.ignore_images = ignore_images

    # we do our own paragraph handling
    html2text.single_line_break = single_line_break

    for key, value in config.items():
        setattr(html2text, key, value)

    lines: Iterable[str] = html2text.handle(html).splitlines()

    # ignore images doesn't catch all images:
    if ignore_images:
        lines = (EMPTY_LINK.sub('', line) for line in lines)

    lines = (l.strip() for l in lines)
    lines = (l for l in lines if VALID_PLAINTEXT_CHARACTERS.search(l))

    # use double newlines to get paragraphs
    plaintext = '\n\n'.join(lines)

    # in an attempt to create proper markdown html2text will escape
    # dots. Since markdown is not something we care about here, we undo that
    plaintext = plaintext.replace('\\.', '.')

    return plaintext
