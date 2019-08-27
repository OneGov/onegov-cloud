from lxml import etree
from wtforms import ValidationError


XSLT_BASE = """<?xml version="1.0" encoding="UTF-8"?>

    <xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:i18n="http://xml.zope.org/namespaces/i18n"
    xmlns:metal="http://xml.zope.org/namespaces/metal"
    xmlns:tal="http://xml.zope.org/namespaces/tal">

    <xsl:template match="@*|node()" name="identity">
      <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
      </xsl:copy>
    </xsl:template>

    <xsl:template match="page">
      <div class="homepage">
        <xsl:apply-templates select="@*|node()"/>
      </div>
    </xsl:template>

    {}

    </xsl:stylesheet>

"""


XML_BASE = """<?xml version="1.0" encoding="UTF-8"?>

    <page xmlns:i18n="http://xml.zope.org/namespaces/i18n"
          xmlns:metal="http://xml.zope.org/namespaces/metal"
          xmlns:tal="http://xml.zope.org/namespaces/tal">

          {}

    </page>
"""

# the number of lines from the start of XML_Base to where the structure is
# injected (for correct line error reporting on the UI side)
XML_LINE_OFFSET = 6


def parse_structure(widgets, structure):
    """ Takes the XML homepage structure and returns the parsed etree xml.

    Raises a wtforms.ValidationError if there's an element which is not
    supported.

    We could do this with DTDs but we don't actually need to, since we only
    care to not include any unknown tags.

    Note that we *try* to make sure that this is no vector for remote code
    execution, but we ultimately do not guarantee it can't happen.

    This xml structure is meant to be static or possibly changeable by admins.
    Ordinary users should not be able to influence this structure.

    """

    valid_tags = {w.tag for w in widgets}
    valid_tags.add('page')  # wrapper element
    valid_tags.add('link')  # doesn't exist as a widget

    # should not be possible anyway, but let's be extra sure
    # (<?python can be used in chameleon to write python code)
    if '<?' in structure:
        raise ValidationError("Invalid element '<?'")

    # do not allow chameleon variables
    if '${' in structure:
        raise ValidationError("Chameleon variables are not allowed")

    xml = XML_BASE.format(structure)
    xml = etree.fromstring(xml.encode('utf-8'))

    for element in xml.iter():
        for attrib in element.attrib:
            if ':' in attrib:
                raise ValidationError("Namespaced attributes are not allowed")

        if element.tag not in valid_tags:
            raise ValidationError("Invalid element '<{}>'".format(element.tag))

    return xml


def transform_homepage_structure(app, structure):
    """ Takes the XML homepage structure and transforms it into a
    chameleon template.

    The app is required as it contains the available widgets.

    """
    widgets = app.config.homepage_widget_registry.values()

    xslt = XSLT_BASE.format('\n'.join(w.template for w in widgets))
    xslt = etree.fromstring(xslt.encode('utf-8'))

    template = etree.XSLT(xslt)(parse_structure(widgets, structure))

    return etree.tostring(template, encoding='unicode', method='xml')


def inject_widget_variables(layout, structure, variables=None):
    """ Takes the layout, structure and a dict of variables meant for the
    template engine and injects the variables required by the widgets, if
    the widgets are indeed in use.

    """

    if not structure:
        return variables

    variables = variables or {}

    for tag, widget in layout.app.config.homepage_widget_registry.items():
        if '<{}'.format(tag) in structure:
            if hasattr(widget, 'get_variables'):
                for key, value in widget.get_variables(layout).items():
                    assert key not in variables, "use unique variable names"
                    variables[key] = value

    return variables
