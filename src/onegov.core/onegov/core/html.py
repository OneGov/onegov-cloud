from bleach import clean as html_clean


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
    'strong',
    'sup',
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


def sanitize_html(html):
    """ Takes the given html and strips all but a whitelisted number of tags
    from it.

    """

    return html_clean(html, tags=SANE_HTML_TAGS, attributes=SANE_HTML_ATTRS)


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

    return svg
