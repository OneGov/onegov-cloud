import bleach


def sanitize_html(html):
    """ Takes the given html and strips all but a whitelisted number of tags
    from it.

    """

    if not html:
        return html

    allowed_tags = [
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

    allowed_attributes = {
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title'],
        'img': ['src', 'alt', 'title']
    }

    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)


def linkify(text):
    """ Takes plain text and injects html links for urls and email addresses.

    """

    if not text:
        return text

    return bleach.linkify(text, parse_email=True)
