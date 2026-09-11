from __future__ import annotations

import re
import turbohtml

from markupsafe import Markup
from turbohtml.clean import Policy, sanitize


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable


# html tags allowed by our default sanitize policy
SANE_HTML_TAGS = frozenset({
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
    'sub',
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
})

# html attributes allowed by our default sanitize policy
SANE_HTML_ATTRS = {
    'a': frozenset({'href', 'title'}),
    'abbr': frozenset({'title', }),
    'acronym': frozenset({'title', }),
    'img': frozenset({'src', 'alt', 'title'}),
    'p': frozenset({'class'}),
    'ol': frozenset({'class'}),
}

# lines without these plaintext characters are excluded in html_to_text
# not re.VERBOSE: its whitespace stays literal inside a character class
VALID_PLAINTEXT_CHARACTERS = re.compile(
    r'['
    r'\d'  # decimals
    r'\w'  # words
    r'\n'  # new lines

    # emojis
    r'\U00002300-\U000023FF'  # misc technical (watch, hourglass, media)
    r'\U00002600-\U000027BF'  # misc symbols + dingbats
    r'\U00002B00-\U00002BFF'  # misc symbols and arrows (stars, arrows)
    r'\U0001F100-\U0001F1FF'  # enclosed alphanumeric supplement (flags)
    r'\U0001F300-\U0001F64F'  # misc symbols/pictographs + emoticons
    r'\U0001F900-\U0001F9FF'  # supplemental symbols/pictographs
    r'\U0001FA70-\U0001FAFF'  # symbols and pictographs extended-A
    r']+'
)

# match empty link expressions
EMPTY_LINK = re.compile(r'\[\]\([^)]+\)')


sanitize_policy = Policy(
    tags=SANE_HTML_TAGS,
    attributes=SANE_HTML_ATTRS
)


def sanitize_html(html: str | None) -> Markup:
    """ Takes the given html and strips all but a whitelisted number of tags
    from it.

    """

    return Markup(sanitize(html or '', sanitize_policy))  # nosec: B704


def sanitize_svg[T: str](svg: T) -> T:
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
    body_width: int = 0,
    ignore_images: bool = True,
    single_line_break: bool = True,
    ignore_emphasis: bool = False,
    ul_item_mark: str = '*',
    strong_mark: str = '**',
    emphasis_mark: str = '_',
) -> str:
    """ Takes the given HTML text and extracts the text from it.

    The result is markdown. The driver behind it is turbohtml.

    """

    config = turbohtml.Markdown(
        document=turbohtml.Markdown.Document(
            # NOTE: While we used to have unicode_snob set to True
            #       it only made sure html entities are converted
            #       to their unicode representation, it didn't actually
            #       replace unicode characters with ASCII, and we don't
            #       really want that to happen anyways. turbohtml
            #       always replaces html entities, so transliteration
            #       is not what we want, since it would replace
            #       things like umlauts and accents with their
            #       unaccented counterparts.
            transliterate=False,
            block_spacing='double',
        ),
        wrapping=turbohtml.Markdown.Wrapping(width=body_width),
        inline=turbohtml.Markdown.Inline(
            strong=strong_mark,
            emphasis=emphasis_mark,
            ignore_emphasis=ignore_emphasis
        ),
        # NOTE: We don't care about producing valid markdown as much
        #       as producing something human-readable, the escaped
        #       markdown would be a nuisance. This minimizes the
        #       amount of escaping that will happen, although it would
        #       be nice to have a `mode='none' that will attemp no
        #       escaping whatsoever.
        escaping=turbohtml.Markdown.Escaping(
            mode='minimal',
            asterisks=False,
            underscores=False,
        ),
        lists=turbohtml.Markdown.Lists(bullets=ul_item_mark),
        images=turbohtml.Markdown.Images(
            mode='ignore' if ignore_images else 'markdown'
        ),
        # NOTE: Using a padded whitespace only table produces more sane
        #       output, since markdown mode tries to preserve the
        #       table working correctly. But markdown doesn't support
        #       multiple lines per table cell or nested tables, both
        #       are very common input, so we will get something very
        #       messy and unreadable, unless we switch to this mode.
        tables=turbohtml.Markdown.Tables(
            mode='strip',
            header='detect',
            pad=True
        ),
    )

    lines: Iterable[str]
    lines = turbohtml.parse(html).to_markdown(config).splitlines()

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
