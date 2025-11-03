from __future__ import annotations

from lxml import etree
from onegov.core.utils import scan_morepath_modules
from onegov.core.widgets import transform_structure
from onegov.org import OrgApp


def test_widgets() -> None:

    class App(OrgApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()
    result = transform_structure(widgets, """
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
    assert a.text is not None
    assert 'Seantis' in a.text

    assert small.tag == 'small'
    assert small.text is not None
    assert 'About' in small.text
