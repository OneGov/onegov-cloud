import re

from bleach.sanitizer import Cleaner
from html2text import HTML2Text

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
    'h6'
]

# html attributes allowed by bleach
SANE_HTML_ATTRS = {
    'a': ['href', 'title'],
    'abbr': ['title', ],
    'acronym': ['title', ],
    'img': ['src', 'alt', 'title']
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
EMPTY_LINK = re.compile(r"\[\]\([^)]+\)")


cleaner = Cleaner(
    tags=SANE_HTML_TAGS,
    attributes=SANE_HTML_ATTRS
)


def sanitize_html(html):
    """ Takes the given html and strips all but a whitelisted number of tags
    from it.

    """

    return cleaner.clean(html)


def sanitize_svg(svg):
    """ I couldn't find a good svg sanitiser function yet, so for now
    this function will be a no-op, though it will try to detect
    svg files which are harmful.

    I tried to go with bleach/html5lib, but the lack of xml namespace support
    makes those options a no go.

    In the future we want a proper SVG sanitiser here!

    """

    assert 'javascript:' not in svg
    assert 'CDATA' not in svg
    assert '<script>' not in svg
    assert 'Set-Cookie' not in svg

    return svg


def html_to_text(html, **config):
    """ Takes the given HTML text and extracts the text from it.

    The result is markdown. The driver behind it is html2text. Have a look
    at https://github.com/Alir3z4/html2text/blob/master/html2text/__init__.py
    to see all options.

    """

    # filter out duplicated lines and lines without any text
    html2text = HTML2Text()

    # output unicode directly, instead of approximating it to ASCII
    config.setdefault('unicode_snob', True)

    # do not wrap lines after a certain length
    config.setdefault('body_width', 0)

    # images are just converted into somewhat useless links, so disable
    config.setdefault('ignore_images', True)

    # we do our own paragraph handling
    config.setdefault('single_line_break', True)

    for key, value in config.items():
        setattr(html2text, key, value)

    lines = html2text.handle(html).splitlines()

    # ignore images doesn't catch all images:
    if config['ignore_images']:
        lines = (EMPTY_LINK.sub('', line) for line in lines)

    lines = (l.strip() for l in lines)
    lines = (l for l in lines if VALID_PLAINTEXT_CHARACTERS.search(l))

    # use double newlines to get paragraphs
    plaintext = '\n\n'.join(lines)

    # in an attempt to create proper markdown html2text will escape
    # dots. Since markdown is not something we care about here, we undo that
    plaintext = plaintext.replace('\\.', '.')

    return plaintext
