from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.town6.conftest import Client


def test_view_information_architecture(client: Client) -> None:

    assert client.get(
        '/information-architecture',
        expect_errors=True
    ).status_code == 403

    client.login_admin()

    page = client.get('/information-architecture')
    assert 'information-architecture' in page
    assert '/information-architecture-json' in page

    assert 'Informationsarchitektur' in page

    # the chart is drawn by the browser, the buttons act on it
    assert {button.attrib['data-chart-action']
            for button in page.pyquery('[data-chart-action]')} == {
        'expand', 'collapse', 'fit', 'reset', 'export', 'export-svg'}

    # the menu link shares the class, the chart is found by its url
    container = page.pyquery('.information-architecture[data-url]')
    assert len(container) == 1
    assert container[0].attrib['data-url'] == (
        'http://localhost/information-architecture-json')

    # charts too large for a png are sent to the svg download
    assert 'SVG' in container[0].attrib['data-export-error-message']
    assert 'hidden' in page.pyquery('.chart-message')[0].attrib

    # the drill down starts hidden, the nodes are drawn by the browser
    assert container[0].attrib['data-drilldown-label']
    assert container[0].attrib['data-drillup-label']
    assert 'hidden' in page.pyquery('[data-chart-action="reset"]')[0].attrib

    nodes = client.get('/information-architecture-json').json['nodes']
    by_name = {node['name']: node for node in nodes}

    assert nodes[0]['id'] == 'root'
    assert by_name['Kontakt']['url'] == 'http://localhost/topics/kontakt'
