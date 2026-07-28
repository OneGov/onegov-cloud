from __future__ import annotations

import transaction
import pytest

from pathlib import Path
from onegov.page import PageCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared import ExtendedBrowser
    from .conftest import Client


def test_information_architecture_is_private(client: Client) -> None:
    anonymous = client.spawn()
    anonymous.get('/information-architecture', status=403)
    anonymous.get('/information-architecture-data', status=403)

    client.login_editor()
    view = client.get('/information-architecture')

    assert view.status_code == 200
    assert view.pyquery('#information-architecture-tree')
    assert 'Informationsarchitektur' in view
    assert 'URL-Hierarchie' in view
    assert (
        view.pyquery('#information-architecture-tree').attr('data-url')
        == 'http://localhost/information-architecture-data'
    )

    homepage = client.get('/')
    information_architecture_links = homepage.pyquery(
        'a[href="http://localhost/information-architecture"]'
    )
    assert len(information_architecture_links) == 1
    assert homepage.pyquery(
        '#modules-dropdown a.information-architecture'
    )


def test_information_architecture_data_contains_full_tree(
    client: Client
) -> None:
    services_lead = 'Distinctive lead for the services topic'
    team_lead = 'Distinctive lead for the team topic'
    news_lead = 'Distinctive lead for the news item'
    news_root_lead = 'Distinctive lead for the news route'
    homepage_lead = 'Distinctive lead for the homepage'
    pages = PageCollection(client.app.session())
    services = pages.add(
        parent=None,
        title='Services',
        type='topic',
        meta={'trait': 'page', 'access': 'private'},
        lead=services_lead
    )
    team = pages.add(
        parent=services,
        title='Team',
        type='topic',
        meta={'trait': 'page'},
        lead=team_lead
    )
    client.app.session().flush()
    services_id = services.id
    team_id = team.id
    news_root = pages.by_path('/news/', ensure_type='news')
    assert news_root is not None
    news_root_id = news_root.id
    news_root.content['lead'] = news_root_lead
    client.app.org.og_description = homepage_lead
    news_item = pages.add(
        parent=news_root,
        title='Architecture test news',
        type='news',
        meta={'trait': 'news'},
        lead=news_lead
    )
    news_item_id = news_item.id
    transaction.commit()

    client.login_admin()
    payload = client.get('/information-architecture-data').json

    assert payload['tree']['id'] == 'homepage'
    assert payload['tree']['title'] == 'Govikon'
    assert payload['tree']['path'] == '/'
    assert payload['tree']['lead'] == homepage_lead
    assert payload['labels']['horizontal'] == 'Von links nach rechts'
    assert payload['labels']['route'] == 'URL-Pfad'
    assert payload['labels']['clear_search'] == 'Suche löschen'
    assert payload['labels']['search_results'] == 'Suchergebnisse'
    assert payload['labels']['expand_branch'] == 'Zweig ausklappen'
    assert payload['labels']['collapse_branch'] == 'Zweig einklappen'
    assert payload['labels']['export_image'] == 'Als Bild exportieren'
    assert payload['labels']['exporting_image'] == 'Bild wird exportiert…'
    assert payload['labels']['export_error'] == (
        'Das Bild konnte nicht exportiert werden.'
    )
    assert [
        child['id'] for child in payload['tree']['children']
    ] == ['route-topics', 'route-news']

    def by_id(node: dict[str, Any], node_id: str) -> dict[str, Any]:
        if node['id'] == node_id:
            return node
        for child in node['children']:
            try:
                return by_id(child, node_id)
            except KeyError:
                pass
        raise KeyError(node_id)

    services_node = by_id(payload['tree'], f'page-{services_id}')
    team_node = by_id(payload['tree'], f'page-{team_id}')
    news_item_node = by_id(payload['tree'], f'page-{news_item_id}')
    topics_route = by_id(payload['tree'], 'route-topics')
    news_route = by_id(payload['tree'], 'route-news')

    assert topics_route['path'] == '/topics'
    assert topics_route['url'] is None
    assert topics_route['kind'] == 'route'
    assert services_node in topics_route['children']
    assert services_node['path'] == '/topics/services'
    assert services_node['url'] == 'http://localhost/topics/services'
    assert services_node['access'] == 'private'
    assert services_node['lead'] == services_lead
    assert team_node['path'] == '/topics/services/team'
    assert team_node in services_node['children']
    assert team_node['lead'] == team_lead
    assert news_route['path'] == '/news'
    assert news_route['url'] == 'http://localhost/news/'
    assert news_route['backing_page_id'] == news_root_id
    assert news_route['page_kind'] == 'news'
    assert news_route['title'] == '/news'
    assert news_route['lead'] == news_root_lead
    assert news_route['children']
    assert all(
        child['kind'] == 'news'
        for child in news_route['children']
    )
    assert news_item_node in news_route['children']
    assert news_item_node['lead'] == news_lead
    with pytest.raises(KeyError):
        by_id(payload['tree'], f'page-{news_root_id}')


@pytest.mark.xdist_group(name='browser')
def test_information_architecture_renders_in_browser(
    browser: ExtendedBrowser,
    client: Client
) -> None:
    long_title = (
        'Municipal services and administrative information for residents '
        'moving into and out of the community throughout the calendar year'
    )
    topic_lead = (
        'This deliberately long topic lead explains where residents can '
        'find municipal services, responsible offices, opening hours, and '
        'further guidance, so the complete text needs substantially more '
        'than two lines in the narrow information architecture card.'
    )
    news_child_title = 'News item used to verify route collapsing'
    news_child_lead = (
        'This deliberately long news lead describes the announcement, its '
        'background, the residents affected by it, and where to find more '
        'information, so it also extends well beyond the two-line preview.'
    )
    pages = PageCollection(client.app.session())
    pages.add(
        parent=None,
        title=long_title,
        type='topic',
        meta={'trait': 'page'},
        lead=topic_lead
    )
    news_root = pages.by_path('/news/', ensure_type='news')
    assert news_root is not None
    pages.add(
        parent=news_root,
        title=news_child_title,
        type='news',
        meta={'trait': 'news'},
        lead=news_child_lead
    )
    transaction.commit()

    browser.login_admin()
    browser.visit('/information-architecture')

    def wait_for_lead_state(lead: str, state: str) -> None:
        browser.page.wait_for_function(
            """({lead, state}) => {
                const element = [...document.querySelectorAll(
                    '.ia-node__lead'
                )].find((candidate) => candidate.textContent === lead);
                if (!element) {
                    return false;
                }

                const style = getComputedStyle(element);
                const bounds = element.getBoundingClientRect();
                const opacity = Number.parseFloat(style.opacity);
                const lineHeight = Number.parseFloat(style.lineHeight);
                const visible = style.display !== 'none' &&
                    style.visibility === 'visible' &&
                    opacity >= .99 &&
                    bounds.width > 0 && bounds.height > 0;
                if (!visible || !Number.isFinite(lineHeight)) {
                    return false;
                }

                const clipped = element.scrollHeight >
                    element.clientHeight + 1;
                if (state === 'preview') {
                    return clipped &&
                        element.clientHeight >= lineHeight * 1.75 &&
                        element.clientHeight <= lineHeight * 2.25;
                }
                return state === 'full' && !clipped &&
                    element.clientHeight > lineHeight * 2.25;
            }""",
            arg={'lead': lead, 'state': state},
            timeout=10000
        )

    nodes = browser.page.locator('.react-flow__node-page')
    nodes.first.wait_for(timeout=10000)

    assert nodes.count() > 1
    toolbar_layout_buttons = browser.page.locator(
        '.ia-tree__toolbar .ia-tree__layout-button'
    )
    assert toolbar_layout_buttons.count() == 2
    assert browser.page.locator(
        '.ia-tree__canvas .ia-tree__layout-button'
    ).count() == 0
    routes = browser.page.locator('.ia-node--route')
    assert routes.count() == 2
    route_text = ' '.join(routes.all_text_contents())
    assert '/topics' in route_text
    assert '/news' in route_text

    news_child = browser.page.locator(
        '.react-flow__node-page', has_text=news_child_title
    )
    assert news_child.count() == 0

    expand_news = browser.page.get_by_role(
        'button', name='Zweig ausklappen: /news', exact=True
    )
    expand_news.wait_for(state='visible', timeout=10000)
    assert expand_news.get_attribute('aria-expanded') == 'false'
    expand_news.click()

    news_child.wait_for(state='visible', timeout=10000)
    news_card = news_child.locator('.ia-node')
    news_lead = news_card.locator('.ia-node__lead')
    assert news_lead.count() == 1
    assert news_lead.text_content() == news_child_lead
    wait_for_lead_state(news_child_lead, 'preview')

    news_card.hover()
    wait_for_lead_state(news_child_lead, 'full')
    browser.page.locator('.ia-tree__toolbar').hover()
    wait_for_lead_state(news_child_lead, 'preview')

    assert browser.page.locator('.ia-node__path').count() == 0
    collapse_news = browser.page.get_by_role(
        'button', name='Zweig einklappen: /news', exact=True
    )
    collapse_news.wait_for(state='visible', timeout=10000)
    assert collapse_news.get_attribute('aria-expanded') == 'true'
    collapse_news.click()

    news_child.wait_for(state='detached', timeout=10000)
    expand_news.wait_for(state='visible', timeout=10000)
    assert expand_news.get_attribute('aria-expanded') == 'false'

    long_title_element = browser.page.locator(
        '.ia-node__title', has_text=long_title
    )
    assert long_title_element.text_content() == long_title
    topic_card = long_title_element.locator('..')
    topic_lead_element = topic_card.locator('.ia-node__lead')
    assert topic_lead_element.count() == 1
    assert topic_lead_element.text_content() == topic_lead
    wait_for_lead_state(topic_lead, 'preview')

    topic_card.focus()
    browser.page.keyboard.press('Tab')
    browser.page.keyboard.press('Shift+Tab')
    assert topic_card.evaluate(
        'element => document.activeElement === element'
    )
    wait_for_lead_state(topic_lead, 'full')
    topic_card.evaluate('element => element.blur()')
    wait_for_lead_state(topic_lead, 'preview')

    card_metrics = topic_card.evaluate("""element => ({
        clientHeight: element.clientHeight,
        scrollHeight: element.scrollHeight
    })""")
    assert card_metrics['scrollHeight'] <= card_metrics['clientHeight'] + 1
    title_metrics = long_title_element.evaluate("""element => {
        const style = getComputedStyle(element);
        return {
            clientHeight: element.clientHeight,
            lineHeight: parseFloat(style.lineHeight),
            scrollHeight: element.scrollHeight
        };
    }""")
    assert title_metrics['clientHeight'] >= title_metrics['lineHeight'] * 2
    assert title_metrics['scrollHeight'] <= title_metrics['clientHeight'] + 1
    assert long_title_element.evaluate(
        """element => parseFloat(
            getComputedStyle(element.closest('.ia-node')).height
        )"""
    ) > 112

    search = browser.page.get_by_role('searchbox', name='Suche')
    assert search.is_visible()
    search.fill('kontakt')
    matches = browser.page.locator('.ia-node--search-match')
    matches.first.wait_for(timeout=10000)
    assert matches.count() == 1
    assert 'Kontakt' in (matches.first.text_content() or '')
    assert (
        browser.page.locator('.ia-node--search-dimmed').count()
        == nodes.count() - 1
    )
    search_count = browser.page.locator(
        '.ia-tree__search-count'
    ).text_content()
    assert search_count is not None
    match_count, total_count = map(int, search_count.split('/'))
    assert match_count == 1
    assert total_count > nodes.count()
    browser.page.get_by_role('button', name='Suche löschen').click()
    matches.first.wait_for(state='detached', timeout=10000)
    assert search.input_value() == ''
    assert browser.page.locator('.ia-node--search-dimmed').count() == 0

    page_link = browser.page.locator('.ia-node[href*="/topics/"]').first
    assert page_link.is_visible()
    assert page_link.locator('.ia-node__link-icon').is_visible()
    assert page_link.evaluate(
        "element => getComputedStyle(element.parentElement).pointerEvents"
    ) == 'all'
    with browser.page.expect_popup() as popup_info:
        page_link.click()
    linked_page = popup_info.value
    linked_page.wait_for_load_state()
    assert '/topics/' in linked_page.url
    linked_page.close()

    assert browser.page.locator('.react-flow__controls').is_visible()
    minimap = browser.page.locator('.react-flow__minimap')
    assert minimap.is_visible()
    minimap_nodes = minimap.locator('.react-flow__minimap-node')
    minimap_nodes.first.wait_for(timeout=10000)
    assert minimap_nodes.count() == nodes.count()

    browser.page.wait_for_function("""async () => {
        const viewport = document.querySelector('.react-flow__viewport');
        const nodes = document.querySelectorAll('.react-flow__node-page');
        const minimapNodes = document.querySelectorAll(
            '.react-flow__minimap-node'
        );
        const layoutStatus = document.querySelector('.ia-tree__layout-status');
        if (
            !viewport || layoutStatus || nodes.length < 2 ||
            minimapNodes.length !== nodes.length
        ) {
            return false;
        }

        const transform = viewport.style.transform ||
            getComputedStyle(viewport).transform;
        await new Promise((resolve) => window.setTimeout(resolve, 400));
        return transform === (
            viewport.style.transform || getComputedStyle(viewport).transform
        );
    }""", timeout=15000)

    export_button = browser.page.get_by_role(
        'button', name='Als Bild exportieren'
    )
    export_button.wait_for(state='visible', timeout=10000)
    with browser.page.expect_download(timeout=30000) as download_info:
        export_button.click()

    download = download_info.value
    assert download.suggested_filename == (
        'govikon-information-architecture.png'
    )
    download_path = download.path()
    assert download_path is not None
    png_path = Path(download_path)
    with png_path.open('rb') as file:
        assert file.read(8) == b'\x89PNG\r\n\x1a\n'
    assert png_path.stat().st_size > 1024

    vertical_centers = browser.page.evaluate("""() => {
        const homepage = document.querySelector('.ia-node--homepage');
        const topics = [...document.querySelectorAll('.ia-node--route')]
            .find((node) => (
                node.querySelector('.ia-node__title')?.textContent.trim()
                    === '/topics'
            ));
        const center = (element) => {
            const bounds = element.getBoundingClientRect();
            return {
                x: bounds.left + bounds.width / 2,
                y: bounds.top + bounds.height / 2
            };
        };
        return {homepage: center(homepage), topics: center(topics)};
    }""")
    assert vertical_centers['topics']['y'] > (
        vertical_centers['homepage']['y'] + 40
    )

    horizontal = browser.page.locator('.ia-tree__layout-button').nth(1)
    horizontal.click()
    assert horizontal.get_attribute('aria-pressed') == 'true'
    browser.page.wait_for_function("""() => {
        if (document.querySelector('.ia-tree__layout-status')) {
            return false;
        }
        const homepage = document.querySelector('.ia-node--homepage');
        const topics = [...document.querySelectorAll('.ia-node--route')]
            .find((node) => (
                node.querySelector('.ia-node__title')?.textContent.trim()
                    === '/topics'
            ));
        if (!homepage || !topics) {
            return false;
        }
        const homeBounds = homepage.getBoundingClientRect();
        const topicsBounds = topics.getBoundingClientRect();
        return topicsBounds.left > homeBounds.left + 40;
    }""", timeout=10000)

    browser.fail_on_console_errors()
