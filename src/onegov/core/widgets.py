""" Provides widgets.

Widgets are small rendered pieces such as news messages or upcoming events.
They are defined with XLS and can be combinded with simple XML.

A widget is simply a class with a tag and template attribute and optionally
a get_variables method::

    class MyWidget:
        tag = 'my-widget'
        template = (
            '<xsl:template match="my-widget">'
            '    <div tal:attributes="class foo">'
            '        <xsl:apply-templates select="node()"/>'
            '    </div>'
            '</xsl:template>'
        )

        def get_variables(self, layout):
            return {'foo': 'bar'}

XML using the widget tags can then be transformed to chameleon HTML/XML. The
widget variables need to be injected before rendering::

    from onegov.core.templates import PageTemplate
    widgets = [MyWidget()]
    structure = '<my-widget>Hello world!</my-widget>'
    template = PageTemplate(transform_structure(widgets, structure))
    layout = None
    template.render(**inject_variables(widgets, layout, structure))

"""
from __future__ import annotations

from lxml import etree
from wtforms.validators import ValidationError


from typing import overload, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Protocol

    from .layout import Layout
    from .types import RenderData

    class Widget(Protocol):
        @property
        def tag(self) -> str: ...
        @property
        def template(self) -> str: ...


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


def parse_structure(
    widgets: Collection[Widget],
    structure: str
) -> etree._Element:
    """ Takes the XML structure and returns the parsed etree xml.

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
        raise ValidationError('Chameleon variables are not allowed')

    xml = XML_BASE.format(structure)
    xml_tree = etree.fromstring(xml.encode('utf-8'))

    for element in xml_tree.iter():
        for attrib in element.attrib:
            if ':' in attrib:
                raise ValidationError('Namespaced attributes are not allowed')

        if element.tag not in valid_tags:
            raise ValidationError(
                "Invalid element '<{}>'".format(element.tag))  # type:ignore

    return xml_tree


def transform_structure(widgets: Collection[Widget], structure: str) -> str:
    """ Takes the XML structure and transforms it into a chameleon template.

    The app is required as it contains the available widgets.

    """

    xslt_str = XSLT_BASE.format('\n'.join(w.template for w in widgets))
    xslt = etree.fromstring(xslt_str.encode('utf-8'))

    template = etree.XSLT(xslt)(parse_structure(widgets, structure))

    return etree.tostring(template, encoding='unicode', method='xml')


@overload
def inject_variables(
    widgets: Collection[Widget],
    layout: Layout,
    structure: Literal[''] | None,
    variables: None = None,
    unique_variable_names: bool = True
) -> None: ...


@overload
def inject_variables(
    widgets: Collection[Widget],
    layout: Layout,
    structure: Literal[''] | None,
    variables: RenderData,
    unique_variable_names: bool = True
) -> RenderData: ...


@overload
def inject_variables(
    widgets: Collection[Widget],
    layout: Layout,
    structure: str,
    variables: None = None,
    unique_variable_names: bool = True
) -> RenderData | None: ...


@overload
def inject_variables(
    widgets: Collection[Widget],
    layout: Layout,
    structure: str | None,
    variables: RenderData,
    unique_variable_names: bool = True
) -> RenderData: ...


def inject_variables(
    widgets: Collection[Widget],
    layout: Layout,
    structure: str | None,
    variables: RenderData | None = None,
    unique_variable_names: bool = True
) -> RenderData | None:
    """ Takes the widgets, layout, structure and a dict of variables meant
    for the template engine and injects the variables required by the widgets,
    if the widgets are indeed in use.

    """

    if not structure:
        return variables

    variables = variables.copy() if variables is not None else {}

    for widget in widgets:
        if '<{}'.format(widget.tag) in structure:
            if hasattr(widget, 'get_variables'):
                for key, value in widget.get_variables(layout).items():
                    if unique_variable_names:
                        assert key not in variables, 'no unique variable names'
                    variables[key] = value

    return variables
