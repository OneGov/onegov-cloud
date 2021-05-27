from chameleon import PageTemplate
from lxml import etree
from onegov.core.utils import Bunch
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.screen_widgets import ColumnWidget
from onegov.election_day.screen_widgets import H1Widget
from onegov.election_day.screen_widgets import H2Widget
from onegov.election_day.screen_widgets import H3Widget
from onegov.election_day.screen_widgets import HRWidget
from onegov.election_day.screen_widgets import LogoWidget
from onegov.election_day.screen_widgets import RowWidget
from onegov.election_day.screen_widgets import TextWidget


def test_generic_widgets():
    structure = """
        <row class="my-row">
            <column span="1" class="my-first-column">
                <h1 class="my-first-header">
                    <h2 class="my-second-header">
                        <h3 class="my-third-header">Title</h3>
                    </h2>
                </h1>
            </column>
            <column span="1" class="my-second-column">
                <hr class="my-hr"/>
            </column>
            <column span="1" class="my-third-column">
                <logo class="my-logo"/>
            </column>
            <column span="1" class="my-fourth-column">
                <text class="my-text">Lorem</text>
            </column>
        </row>
    """
    widgets = [
        ColumnWidget(),
        H1Widget(),
        H2Widget(),
        H3Widget(),
        HRWidget(),
        LogoWidget(),
        RowWidget(),
        TextWidget()
    ]

    layout = Bunch(
        app=Bunch(logo='logo.svg'),
        request=Bunch(link=lambda x: x)
    )

    data = inject_variables(widgets, layout, structure)
    assert data == {'logo': 'logo.svg'}

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)

    xml = etree.fromstring(result.encode('utf-8'))

    row = next(xml.iterchildren())
    assert row.tag == 'div'
    assert row.attrib == {
        'class': 'row my-row',
        'style': 'max-width: none'
    }

    columns = list(row.iterchildren())
    assert columns[0].tag == 'div'
    assert columns[0].attrib == {
        'class': 'small-12 medium-1 columns my-first-column'
    }
    assert columns[1].tag == 'div'
    assert columns[1].attrib == {
        'class': 'small-12 medium-1 columns my-second-column'
    }
    assert columns[2].tag == 'div'
    assert columns[2].attrib == {
        'class': 'small-12 medium-1 columns my-third-column'
    }
    assert columns[3].tag == 'div'
    assert columns[3].attrib == {
        'class': 'small-12 medium-1 columns my-fourth-column'
    }

    h1 = next(columns[0].iterchildren())
    assert h1.tag == 'h1'
    assert h1.attrib == {
        'class': 'my-first-header'
    }

    h2 = next(h1.iterchildren())
    assert h2.tag == 'h2'
    assert h2.attrib == {
        'class': 'my-second-header'
    }

    h3 = next(h2.iterchildren())
    assert h3.tag == 'h3'
    assert h3.attrib == {
        'class': 'my-third-header'
    }
    assert h3.text == 'Title'

    hr = next(columns[1].iterchildren())
    assert hr.tag == 'hr'
    assert hr.attrib == {
        'class': 'my-hr'
    }

    logo = next(columns[2].iterchildren())
    assert logo.tag == 'img'
    assert logo.attrib == {
        'class': 'my-logo',
        'src': 'logo.svg'
    }

    text = next(columns[3].iterchildren())
    assert text.tag == 'p'
    assert text.attrib == {
        'class': 'my-text'
    }
    assert text.text == 'Lorem'
