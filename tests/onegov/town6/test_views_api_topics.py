import transaction

from copy import deepcopy
from onegov.org.models import Topic


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client
    from pytest import MonkeyPatch


# the linked topics are only synced on page views
HTML = {'Accept': 'text/html'}

API_URL = 'https://onegov.govikon.ch/api/'


def api_item_data(item: dict[str, Any]) -> dict[str, Any]:
    return {entry['name']: entry['value'] for entry in item['data']}


def test_api_topics_parent_filter(client: Client) -> None:
    session = client.app.session()
    roots = session.query(Topic).filter(Topic.parent_id.is_(None))
    roots = roots.order_by(Topic.order)
    root_titles = [topic.title for topic in roots]
    organisation = roots.filter(Topic.name == 'organisation').one()
    children = sorted(
        (c for c in organisation.children),
        key=lambda c: c.order
    )
    organisation_id = organisation.id

    response = client.get('/api/topics?parent=root')
    items = response.json['collection']['items']
    assert [api_item_data(i)['title'] for i in items] == root_titles
    assert all(api_item_data(i)['trait'] for i in items)

    response = client.get(f'/api/topics?parent={organisation_id}')
    items = response.json['collection']['items']
    assert [api_item_data(i)['title'] for i in items] == [
        c.title for c in children]

    client.get('/api/topics?parent=foo', status=400)

    # hidden topics are not returned by id
    item = client.get(f'/api/topics/{organisation_id}').json
    assert api_item_data(item['collection']['items'][0])['title']

    organisation = session.query(Topic).filter_by(id=organisation_id).one()
    organisation.access = 'private'
    transaction.commit()

    client.get(f'/api/topics/{organisation_id}', status=404)


def test_api_topic_link(
    client_with_fts: Client,
    monkeypatch: MonkeyPatch
) -> None:

    source: dict[int, dict[str, Any] | None] = {
        5: {
            'title': 'Energieberatung',
            'trait': 'page',
            'lead': 'Beratung rund um Energie',
            'text': '<p>Wir beraten Sie zu Gebäudehülle und '
                    'Heizungsersatz.</p>',
            'contact': 'Energiefachstelle\nBahnhofstrasse 1',
            'sidepanel_links': [['Förderprogramm', '/topics/foerderung']],
            'sidepanel_contact': [],
            'html_url': 'https://onegov.govikon.ch/'
                        'topics/energieberatung',
        }
    }
    original = deepcopy(source[5])

    def fetch_api_topic(api_url: str, topic_id: int) -> Any:
        assert api_url == API_URL
        return deepcopy(source.get(topic_id))

    registered: dict[str, int] = {}

    def register_api_link(
        api_url: str,
        topic_id: int,
        url: str,
        title: str,
        dry_run: bool = False
    ) -> None:
        if not dry_run:
            registered[url] = topic_id

    def unregister_api_link(api_url: str, topic_id: int, url: str) -> None:
        assert registered.pop(url) == topic_id

    monkeypatch.setattr(
        'onegov.org.api_source.fetch_api_topic', fetch_api_topic)
    monkeypatch.setattr(
        'onegov.org.api_source.register_api_link', register_api_link)
    monkeypatch.setattr(
        'onegov.org.views.page.unregister_api_link', unregister_api_link)

    client = client_with_fts
    client.login_admin()
    anon = client.spawn()

    # the add link is only shown once a source is configured
    page = client.get('/topics/organisation')
    assert 'API-Verknüpfung' not in page

    settings = client.get('/api-source-settings')
    settings.form['api_link_role'] = 'child'
    settings.form['api_source_url'] = API_URL.rstrip('/')
    settings.form.submit().follow()
    assert client.app.org.api_link_role == 'child'
    assert client.app.org.api_source_url == API_URL

    page = client.get('/topics/organisation').click('API-Verknüpfung')
    assert 'api-topic-picker' in page
    assert 'data-api-url="https://onegov.govikon.ch/api/"' \
        in page

    # a topic has to be selected
    page = page.form.submit()
    assert 'Dieses Feld wird benötigt' in page

    page.form['api_topic_id'].force_value('5')
    page = page.form.submit().follow()
    assert 'API-Verknüpfung hinzugefügt' in page
    url = page.request.url
    assert url.endswith('/topics/organisation/energieberatung')

    # the source organisation is told which page links its topic
    assert registered == {url: 5}

    # editors see where the content comes from
    assert 'Gebäudehülle' in page
    assert f'{API_URL[:-4]}editor/edit/page/5' in page
    assert 'Kopieren' not in page

    # visitors see a normal topic
    view = anon.get(url, headers=HTML)
    assert 'Energieberatung' in view
    assert 'Gebäudehülle' in view
    assert 'Energiefachstelle' in view
    assert 'https://onegov.govikon.ch/topics/foerderung' \
        in view
    assert 'editor/edit/page/5' not in view

    search = anon.get('/search', params={'q': 'Gebäudehülle'}, headers=HTML)
    assert '/topics/organisation/energieberatung' in search

    # changes of the source are taken over on the next page view
    assert source[5] is not None
    source[5]['text'] += '<p>Neu auch zu Solarthermie.</p>'
    source[5]['title'] = 'Energieberatung und Förderung'

    search = anon.get('/search', params={'q': 'Solarthermie'}, headers=HTML)
    assert 'Energieberatung und Förderung' in search
    assert 'Solarthermie' in anon.get(url, headers=HTML)

    # a custom title is kept
    edit = client.get(url).click('Bearbeiten')
    assert edit.form['title'].value == ''
    edit.form['title'] = 'Energie'
    edit.form.submit().follow()
    source[5]['title'] = 'Energieberatung (neu)'
    anon.get(url, headers=HTML)
    session = client.app.session()
    topic = session.query(Topic).filter_by(name='energieberatung').one()
    assert topic.title == 'Energie'

    # unavailable topics are hidden from the public and the search
    source[5] = None
    search = anon.get('/search', params={'q': 'Solarthermie'}, headers=HTML)
    assert '/topics/organisation/energieberatung' not in search
    assert anon.get(url, headers=HTML, expect_errors=True).status_code != 200

    page = client.get(url, headers=HTML)
    assert 'zurzeit nicht öffentlich verfügbar' in page

    # and shown again once they are available again
    source[5] = original
    assert 'Gebäudehülle' in anon.get(url, headers=HTML)
    search = anon.get('/search', params={'q': 'Gebäudehülle'}, headers=HTML)
    assert '/topics/organisation/energieberatung' in search

    # deleting the parent page unregisters the linked child pages as well
    assert registered == {url: 5}
    page = client.get('/topics/organisation')
    client.delete(page.pyquery('a.delete-link').attr('ic-delete-from'))
    assert registered == {}


def test_api_topic_link_parent(client: Client) -> None:
    session = client.app.session()
    topic = session.query(Topic).filter_by(name='organisation').one()
    topic_id = topic.id
    links_url = f'/api/topics/{topic_id}/links'
    child = 'https://onegov.meggen.ch/topics/energie'

    # only parent organisations accept links
    client.post_json(links_url, {'url': child}, status=403)

    client.login_admin()
    settings = client.get('/api-source-settings')
    settings.form['api_link_role'] = 'parent'
    settings.form.submit().follow()
    assert client.app.org.api_link_role == 'parent'
    assert client.app.org.api_source_url is None

    anon = client.spawn()

    anon.post_json(links_url, {'url': 'javascript:alert(1)'}, status=403)
    anon.post_json(links_url, {'title': 'Energie'}, status=400)
    anon.post_json('/api/topics/0/links', {'url': child}, status=404)

    # a dry run doesn't store anything
    anon.post_json(links_url, {'url': child, 'dry_run': True})
    assert 'Energie' not in client.get('/topics/organisation')

    anon.post_json(links_url, {'url': child, 'title': 'Energie'})
    anon.post_json(links_url, {'url': child, 'title': 'Energie Meggen'})

    page = client.get('/topics/organisation')
    assert 'api-linked-by-hint' in page
    assert 'Energie Meggen' in page
    assert child in page
    assert 'api-linked-by-hint' not in anon.get('/topics/organisation')

    anon.delete(f'{links_url}?url={child}')
    assert 'api-linked-by-hint' not in client.get('/topics/organisation')
