import bleach

from lxml import etree
from lxml.html import fragments_fromstring


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


def mark_images(html):
    """ Takes the given html and marks every paragraph with an 'has-img'
    class, if the paragraph contains an img element.

    """

    if not html:
        return html

    fragments = fragments_fromstring(html)

    # we perform a root xpath lookup, which will result in all paragraphs
    # being looked at - so we don't need to loop over all elements (yah, it's
    # a bit weird)
    for element in fragments[:1]:

        # instead of failing, lxml will return strings instead of elements if
        # they can't be parsed.. so we have to inspect the objects
        if not hasattr(element, 'xpath'):
            return html

        for paragraph in element.xpath('//p[img]'):
            if 'class' in paragraph.attrib:
                paragraph.attrib['class'] += ' has-img'
            else:
                paragraph.attrib['class'] = 'has-img'

    return ''.join(etree.tostring(e).decode('utf-8') for e in fragments)
