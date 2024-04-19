from lxml import etree
from onegov.core.templates import PageTemplate
from onegov.core.utils import Bunch
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.screen_widgets import GridColumnWidget
from onegov.election_day.screen_widgets import GridRowWidget
from onegov.election_day.screen_widgets import H1Widget
from onegov.election_day.screen_widgets import H2Widget
from onegov.election_day.screen_widgets import H3Widget
from onegov.election_day.screen_widgets import HRWidget
from onegov.election_day.screen_widgets import PrincipalLogoWidget
from onegov.election_day.screen_widgets import PWidget
from onegov.election_day.screen_widgets import QrCodeWidget


def test_generic_widgets():
    structure = """
        <grid-row class="my-row">
            <grid-column span="1" class="my-first-column">
                <h1 class="my-first-header">
                    <h2 class="my-second-header">
                        <h3 class="my-third-header">Title</h3>
                    </h2>
                </h1>
            </grid-column>
            <grid-column span="1" class="my-second-column">
                <hr class="my-hr"/>
            </grid-column>
            <grid-column span="1" class="my-third-column">
                <principal-logo class="my-logo"/>
            </grid-column>
            <grid-column span="1" class="my-fourth-column">
                <p class="my-text">Lorem</p>
            </grid-column>
            <grid-column span="1" class="my-fifth-column">
                '<qr-code class="my-first-qr-code" url="https://a.b"/>'
                '<qr-code class="my-second-qr-code" url="https://c.d"/>'
            </grid-column>
        </grid-row>
    """
    widgets = [
        GridColumnWidget(),
        H1Widget(),
        H2Widget(),
        H3Widget(),
        HRWidget(),
        PrincipalLogoWidget(),
        QrCodeWidget(),
        GridRowWidget(),
        PWidget()
    ]

    layout = Bunch(
        app=Bunch(logo='logo.svg'),
        request=Bunch(link=lambda x: x)
    )

    data = inject_variables(widgets, layout, structure)
    assert len(data) == 2
    assert data['logo'] == 'logo.svg'
    assert data['qr_code']

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
    assert columns[4].tag == 'div'
    assert columns[4].attrib == {
        'class': 'small-12 medium-1 columns my-fifth-column'
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

    qr_codes = list(columns[4].iterchildren())
    assert len(qr_codes) == 2
    assert qr_codes[0].tag == 'img'
    assert qr_codes[1].tag == 'img'
    assert len(qr_codes[0].attrib) == 2
    assert len(qr_codes[1].attrib) == 2
    assert qr_codes[0].attrib['class'] == 'my-first-qr-code'
    assert qr_codes[1].attrib['class'] == 'my-second-qr-code'
    assert qr_codes[0].attrib['src'].startswith('data:image/png;base64,')
    assert qr_codes[1].attrib['src'].startswith('data:image/png;base64,')
    assert qr_codes[0].attrib['src'] != qr_codes[1].attrib['src']
