import pytest

from lxml import etree
from onegov.core.utils import scan_morepath_modules, Bunch
from onegov.org import OrgApp
from onegov.org.homepage_widgets.core import (
    parse_structure,
    inject_widget_variables,
    transform_homepage_structure
)
from wtforms import ValidationError


@pytest.mark.parametrize('invalid_structure', [
    " <panel><?python assert False></panel>",
    "<panel>${{request.password}}</panel>",
    "<panel>${request.password}</panel>",
    "<panel tal:content='request.password'></panel>",
    "<div>html</div>"

])
def test_parse_invalid_structure(invalid_structure):

    class App(OrgApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()

    with pytest.raises(ValidationError):
        parse_structure(widgets, invalid_structure)


def test_inject_widget_variables():

    class App(OrgApp):
        pass

    @App.homepage_widget(tag='foo')
    class FooWidget(object):

        def get_variables(self, layout):
            return {
                'bar': '0xdeadbeef'
            }

    scan_morepath_modules(App)
    App.commit()

    layout = Bunch(app=App())
    assert inject_widget_variables(layout, "") is None
    assert inject_widget_variables(layout, "<foo />") == {'bar': '0xdeadbeef'}
    assert inject_widget_variables(layout, "<foo />", {'foo': 'bar'}) == {
        'foo': 'bar',
        'bar': '0xdeadbeef'
    }
    assert inject_widget_variables(layout, "<panel />") == {}


def test_transform_homepage_structure():

    class App(OrgApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    result = transform_homepage_structure(App(), """
        <row>
            <column span="8">
                <links>
                    <link url="#about" description="About">
                        Seantis
                    </link>
                </links>
            </column>
        </row>
    """)

    xml = etree.fromstring(result.encode('utf-8'))

    for ns in ('i18n', 'metal', 'tal'):
        assert ns in xml.nsmap

    assert xml.attrib['class'] == 'homepage'

    row = next(xml.iterchildren())
    assert row.tag == 'div'
    assert row.attrib['class'] == 'row'

    col = next(row.iterchildren())
    assert col.tag == 'div'
    assert col.attrib['class'] == 'small-12 medium-8 columns'

    ul = next(col.iterchildren())
    assert ul.tag == 'ul'
    assert ul.attrib['class'] == 'panel-links'

    li = next(ul.iterchildren())
    assert li.tag == 'li'

    a, small = li.getchildren()
    assert a.tag == 'a'
    assert a.attrib['href'] == '#about'
    assert 'Seantis' in a.text

    assert small.tag == 'small'
    assert 'About' in small.text
