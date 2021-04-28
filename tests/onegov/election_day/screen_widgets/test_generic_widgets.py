from chameleon import PageTemplate
from lxml import etree
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.screen_widgets import ColumnWidget
from onegov.election_day.screen_widgets import H1Widget
from onegov.election_day.screen_widgets import H2Widget
from onegov.election_day.screen_widgets import H3Widget
from onegov.election_day.screen_widgets import HRWidget
from onegov.election_day.screen_widgets import RowWidget


def test_generic_widgets():
    structure = """
        <row>
            <column span="6"><h1><h2><h3>Title</h3></h2></h1></column>
            <column span="6"><hr /></column>
        </row>
    """
    widgets = [
        ColumnWidget(),
        H1Widget(),
        H2Widget(),
        H3Widget(),
        HRWidget(),
        RowWidget(),
    ]

    data = inject_variables(widgets, None, structure)
    assert data == {}

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)

    xml = etree.fromstring(result.encode('utf-8'))

    row = next(xml.iterchildren())
    assert row.tag == 'div'
    assert row.attrib == {'class': 'row', 'style': 'max-width: none'}

    columns = list(row.iterchildren())
    assert columns[0].tag == 'div'
    assert columns[0].attrib == {'class': 'small-12 medium-6 columns'}

    h1 = next(columns[0].iterchildren())
    assert h1.tag == 'h1'

    h2 = next(h1.iterchildren())
    assert h2.tag == 'h2'

    h3 = next(h2.iterchildren())
    assert h3.tag == 'h3'
    assert h3.text == 'Title'

    assert columns[1].tag == 'div'
    assert columns[1].attrib == {'class': 'small-12 medium-6 columns'}

    hr = next(columns[1].iterchildren())
    assert hr.tag == 'hr'
