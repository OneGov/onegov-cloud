from __future__ import annotations

import transaction

from datetime import timedelta
from onegov.core.utils import normalize_for_url
from onegov.page import PageCollection
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_view_topic_chart(client: Client) -> None:

    assert client.get(
        '/topic-chart',
        expect_errors=True
    ).status_code == 403
    assert client.get(
        '/topic-chart-json',
        expect_errors=True
    ).status_code == 403

    client.login_admin()

    # the view is linked in the modules menu
    assert '/topic-chart' in client.get('/')

    page = client.get('/topic-chart')
    assert 'topic-chart' in page
    assert '/topic-chart-json' in page

    # the menu link shares the class, the chart is found by its url
    assert len(page.pyquery('.topic-chart[data-url]')) == 1

    scripts = [script.attrib['src'] for script in page.pyquery('script[src]')]
    assert any('topic-chart' in script for script in scripts)

    new_page = client.get('/topics/organisation').click('Thema')
    new_page.form['title'] = 'Child Page'
    new_page.form['text'] = 'Child'
    new_page.form.submit()

    nodes = client.get('/topic-chart-json').json['nodes']
    by_name = {node['name']: node for node in nodes}

    print(by_name)

    # the organization itself is the root of the chart
    assert nodes[0]['id'] == 'root'
    assert nodes[0]['parentId'] is None

    assert by_name['Organisation']['parentId'] == 'root'
    assert by_name['Kontakt']['url'] == 'http://localhost/topics/kontakt'
    assert by_name['Kontakt']['access'] == 'public'
    assert by_name['Kontakt']['published'] is True

    assert by_name['Child Page']['parentId'] == by_name['Organisation']['id']
    assert by_name['Child Page']['url'] == (
        'http://localhost/topics/organisation/child-page')
    assert by_name['Child Page']['access'] == 'public'
    assert by_name['Child Page']['published'] is True

    # news are not part of the topic hierarchy
    assert 'Aktuelles' not in by_name


def test_view_topic_chart_actions(client: Client) -> None:

    client.login_admin()
    page = client.get('/topic-chart')

    assert 'Themendiagramm' in page

    # the chart is drawn by the browser, the buttons act on it
    assert {button.attrib['data-chart-action']
            for button in page.pyquery('[data-chart-action]')} == {
        'expand', 'collapse', 'fit', 'reset', 'export', 'export-svg'}

    container = page.pyquery('.topic-chart[data-url]')[0]
    assert container.attrib['data-url'] == 'http://localhost/topic-chart-json'
    assert container.attrib['data-image-name'] == '{}-topic-chart'.format(
        normalize_for_url(client.app.org.name))

    # charts too large for a png are sent to the svg download
    assert 'SVG' in container.attrib['data-export-error-message']
    message = page.pyquery('.chart-message')[0]
    assert 'hidden' in message.attrib

    # the drill down starts hidden, the nodes are drawn by the browser
    assert container.attrib['data-drilldown-label']
    assert container.attrib['data-drillup-label']
    reset = page.pyquery('[data-chart-action="reset"]')[0]
    assert 'hidden' in reset.attrib


def test_view_topic_chart_hidden_topics(client: Client) -> None:

    client.login_admin()

    new_page = client.get('/topics/organisation').click('Thema')
    new_page.form['title'] = 'Secret Page'
    new_page.form['text'] = 'Secret'
    new_page.form['access'] = 'private'
    new_page.form.submit()

    nodes = client.get('/topic-chart-json').json['nodes']
    by_name = {node['name']: node for node in nodes}
    assert by_name['Secret Page']['access'] == 'private'

    # editors see the private page as well, anonymous users never get here
    editor = client.spawn()
    editor.login_editor()
    nodes = editor.get('/topic-chart-json').json['nodes']
    assert 'Secret Page' in {node['name'] for node in nodes}


def test_view_topic_chart_unpublished_topics(client: Client) -> None:

    client.login_admin()

    new_page = client.get('/topics/organisation').click('Thema')
    new_page.form['title'] = 'Expired Page'
    new_page.form['text'] = 'Expired'
    new_page.form.submit()

    pages = PageCollection(client.app.session())
    expired = pages.query().filter_by(title='Expired Page').one()
    expired.publication_end = utcnow() - timedelta(days=1)
    transaction.commit()

    nodes = client.get('/topic-chart-json').json['nodes']
    by_name = {node['name']: node for node in nodes}
    assert by_name['Expired Page']['published'] is False
    assert by_name['Organisation']['published'] is True
