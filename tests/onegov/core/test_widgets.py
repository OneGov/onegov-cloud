from __future__ import annotations

import pytest

from lxml import etree
from onegov.core.widgets import inject_variables
from onegov.core.widgets import parse_structure
from onegov.core.widgets import transform_structure
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData


class TextWidget:
    tag = 'text'
    template = """
        <xsl:template match="text">
            <div class="text">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@pytest.mark.parametrize('invalid_structure', [
    " <panel><?python assert False></panel>",
    "<panel>${{request.password}}</panel>",
    "<panel>${request.password}</panel>",
    "<panel tal:content='request.password'></panel>",
    "<div>html</div>"

])
def test_parse_invalid_structure(invalid_structure: str) -> None:

    widgets = [TextWidget()]

    with pytest.raises(ValidationError):
        parse_structure(widgets, invalid_structure)


def test_inject_variables() -> None:

    class FooWidget:
        tag = 'foo'
        template: str

        def get_variables(self, layout: object) -> RenderData:
            return {
                'bar': '0xdeadbeef'
            }

    widgets = [FooWidget()]
    layout: Any = None
    inject = inject_variables
    assert inject(widgets, layout, "") is None
    assert inject(widgets, layout, "<foo />") == {
        'bar': '0xdeadbeef'
    }
    assert inject(widgets, layout, "<foo />", {'foo': 'bar'}) == {
        'foo': 'bar',
        'bar': '0xdeadbeef'
    }
    with pytest.raises(AssertionError):
        assert inject(widgets, layout, "<foo />", {'bar': 'bar'}) == {
            'bar': '0xdeadbeef'
        }
    assert inject(widgets, layout, "<foo />", {'bar': 'bar'}, False) == {
        'bar': '0xdeadbeef'
    }
    assert inject(widgets, layout, "<bar />") == {}


def test_transform_structure() -> None:

    widgets = [TextWidget()]
    result = transform_structure(widgets, """
        <text>
            <text>Some text</text>
        </text>
    """)
    xml = etree.fromstring(result.encode('utf-8'))

    for ns in ('i18n', 'metal', 'tal'):
        assert ns in xml.nsmap

    assert xml.attrib['class'] == 'homepage'

    text = next(xml.iterchildren())
    assert text.tag == 'div'
    assert text.attrib['class'] == 'text'

    subtext = next(text.iterchildren())
    assert subtext.tag == 'div'
    assert subtext.attrib['class'] == 'text'
    assert subtext.text == 'Some text'
