from lxml import etree
from lxml.html import fragments_fromstring

from onegov.core import utils
from purl import URL


def mark_images(html):
    """ Takes the given html and marks every paragraph with an 'has-img'
    class, if the paragraph contains an img or iframe element.

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

        for paragraph in element.xpath('//p[img|iframe]'):
            if 'class' in paragraph.attrib:
                paragraph.attrib['class'] += ' has-img'
            else:
                paragraph.attrib['class'] = 'has-img'

    return ''.join(etree.tostring(e).decode('utf-8') for e in fragments)


def sanitize_html(html):
    """ Extends the core's sanitize html with extra allowed attributes. """

    from onegov.town.path import map_expr

    def is_allowed_iframe_attribute(name, value):
        if name in {'id', 'class', 'scrolling'}:
            return True

        if name == 'src':
            return map_expr.search(URL(value).path()) and True or False

        return False

    return utils.sanitize_html(
        html,
        additional_tags=['iframe'],
        additional_attributes=dict(
            iframe=is_allowed_iframe_attribute
        ))
