from lxml import etree
from lxml.html import fragments_fromstring


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
