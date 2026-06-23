from __future__ import annotations

import json
import transaction
from base64 import b64encode
from datetime import timedelta
from collection_json import Collection  # type: ignore[import-untyped]
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.form import FormCollection
from onegov.org.models.external_link import (
    ExternalFormLink, ExternalResourceLink)
from onegov.people import Person
from sedate import utcnow
from tests.onegov.api.test_views import patch_collection_json  # noqa: F401
from unittest.mock import patch
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client
    from onegov.agency import AgencyApp
    from onegov.org.models import ExtendedDirectory
    from unittest.mock import MagicMock


def get_base64_encoded_json_string(data: Any) -> str:
    return b64encode(json.dumps(data).encode('ascii')).decode('ascii')


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.broadcast')
@patch('onegov.websockets.integration.authenticate')
def test_view_api(
    authenticate: MagicMock,
    broadcast: MagicMock,
    connect: MagicMock,
    client: Client
) -> None:

    client.login_admin()  # prevent rate limit

    def collection(url: str) -> Collection:
        return Collection.from_json(client.get(url).body)

    def data(item: Any) -> dict[str, Any]:
        return {x.name: x.value for x in item.data}

    def filters(item: Any) -> dict[str, Any]:
        return {x.name: x.values or x.prompt for x in item.data}

    def links(item: Any) -> dict[str, str]:
        return {x.rel: x.href for x in item.links}

    def template(item: Any) -> set[str]:
        return {x.name for x in item.template.data}

    endpoints = collection('/api')
    assert len(endpoints.queries) == 6

    # Endpoints with query hints
    assert endpoints.queries[0].rel == 'events'
    assert endpoints.queries[0].href == 'http://localhost/api/events'
    assert filters(endpoints.queries[0]).keys() == {
        'start',
        'end',
        'highlight',
        'locations',
        'sources',
        'syndicate',
        'tags',
    }
    # Additional endpoints
    assert endpoints.queries[1].rel == 'forms'
    assert endpoints.queries[1].href == 'http://localhost/api/forms'
    assert not endpoints.queries[1].data
    assert endpoints.queries[2].rel == 'news'
    assert endpoints.queries[2].href == 'http://localhost/api/news'
    assert not endpoints.queries[2].data
    assert endpoints.queries[3].rel == 'people'
    assert endpoints.queries[3].href == 'http://localhost/api/people'
    assert not endpoints.queries[3].data
    assert endpoints.queries[4].rel == 'resources'
    assert endpoints.queries[4].href == 'http://localhost/api/resources'
    assert not endpoints.queries[4].data
    assert endpoints.queries[5].rel == 'topics'
    assert endpoints.queries[5].href == 'http://localhost/api/topics'
    assert not endpoints.queries[5].data

    # Configure event filters
    settings = client.get('/event-settings')
    settings.form['event_filter_type'] = 'filters'
    settings.form.submit().follow()

    events_page = client.get('/events')
    filter_settings = events_page.click('Konfigurieren')
    filter_settings.form[
        'definition'
    ] = """
        Altersgruppe =
            [ ] Kind
            [ ] Jugend
            [ ] Familie
            [ ] Alter

        Empfehlung =
            [ ] Ja
    """
    filter_settings.form['keyword_fields'].value = 'Altersgruppe\nEmpfehlung'
    filter_settings.form.submit().follow()

    endpoints = collection('/api')
    event_fiters = filters(endpoints.queries[0])
    assert event_fiters.keys() == {
        'start',
        'end',
        'highlight',
        'locations',
        'sources',
        'syndicate',
        'altersgruppe',
        'empfehlung',
    }
    assert event_fiters['altersgruppe'] == [
        'Kind',
        'Jugend',
        'Familie',
        'Alter'
    ]
    assert event_fiters['empfehlung'] == ['Ja']
    # Configure tags and filters
    settings = client.get('/event-settings')
    settings.form['event_filter_type'] = 'tags_and_filters'
    settings.form.submit().follow()

    endpoints = collection('/api')
    assert filters(endpoints.queries[0]).keys() == {
        'start',
        'end',
        'highlight',
        'locations',
        'sources',
        'syndicate',
        'tags',
        'altersgruppe',
        'empfehlung',
    }

    # Events
    # TODO: Test with custom content and get rid of implicit dependency
    #       on initial content.
    events = {
        item.data[0].value: item.href
        for item in collection('/api/events').items
    }
    assert set(events) == {
        '150 Jahre Govikon',
        'Generalversammlung',
        'Gemeinsames Turnen',
        'Fussballturnier'
    }

    celebration = collection(events['150 Jahre Govikon']).items[0]
    celebration_data = data(celebration)
    assert celebration_data['title'] == '150 Jahre Govikon'
    assert celebration_data['tags'] == ['Party']
    assert celebration_data['organizer'] == 'Govikon'
    assert celebration_data['location'] == 'Sportanlage'

    # TODO: Test start/end filters

    # test event filter locations
    assert {
        item.data[0].value
        for item in collection(
            '/api/events?locations=Sportanlage').items
    } == {'150 Jahre Govikon', 'Fussballturnier'}

    # test event filter sources
    # TODO: Test sources properly with custom events
    assert {
        item.data[0].value
        for item in collection(
            '/api/events?sources=Sportverein+Govikon').items
    } == set()

    # test event filter tags
    assert {
        item.data[0].value
        for item in collection(
            '/api/events?tags=Party').items
    } == {'150 Jahre Govikon'}

    # test event custom filter
    # TODO: Test custom filters properly with custom events
    assert {
        item.data[0].value
        for item in collection(
            '/api/events?altersgruppe=Kind&altersgruppe=Jugend').items
    } == set()

    # News
    # TODO: Test with custom content and get rid of implicit dependency
    #       on initial content.
    assert {
        item.data[0].value
        for item in collection('/api/news').items
    } == {'Wir haben eine neue Webseite!'}

    # Topics
    # TODO: Test with custom content and get rid of implicit dependency
    #       on initial content.
    topics = {
        data(item)['title']
        for item in collection('/api/topics').items
    } == {'Organisation', 'Themen', 'Kontakt'}


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.broadcast')
@patch('onegov.websockets.integration.authenticate')
def test_api_syndicate_filter(
    authenticate: MagicMock,
    broadcast: MagicMock,
    connect: MagicMock,
    client: Client[AgencyApp],
) -> None:

    client.login_admin()

    def collection(url: str) -> Collection:
        return Collection.from_json(client.get(url).body)

    def data(item: Any) -> dict[str, Any]:
        return {x.name: x.value for x in item.data}

    all_titles = {
        item.data[0].value for item in collection('/api/events').items
    }
    assert len(all_titles) == 4

    # no events are syndicated by default
    assert not collection('/api/events?syndicate=true').items

    # all events returned for syndicate=false
    assert {
        item.data[0].value
        for item in collection('/api/events?syndicate=false').items
    } == all_titles

    # mark one event for syndication via the edit form
    events_page = client.get('/events')
    event_page = events_page.click('150 Jahre Govikon')
    edit_page = event_page.click('Bearbeiten')
    edit_page.form['syndicate'] = True
    edit_page.form.submit()

    # syndicate=true returns only the marked event
    assert {
        item.data[0].value
        for item in collection('/api/events?syndicate=true').items
    } == {'150 Jahre Govikon'}

    # syndicate=false excludes the marked event
    assert {
        item.data[0].value
        for item in collection('/api/events?syndicate=false').items
    } == all_titles - {'150 Jahre Govikon'}

    # syndicate is exposed in item data
    events = {
        item.data[0].value: item.href
        for item in collection('/api/events').items
    }
    celebration = collection(events['150 Jahre Govikon']).items[0]
    assert data(celebration)['syndicate'] is True

    gym = collection(events['Gemeinsames Turnen']).items[0]
    assert data(gym)['syndicate'] is False

    # --- highlight filter ---
    # no events are highlighted by default
    assert not collection('/api/events?highlight=true').items

    # all events returned for highlight=false
    assert {
        item.data[0].value
        for item in collection('/api/events?highlight=false').items
    } == all_titles

    # mark one event as highlighted via the edit form
    events_page = client.get('/events')
    event_page = events_page.click('Fussballturnier')
    edit_page = event_page.click('Bearbeiten')
    edit_page.form['highlight'] = True
    edit_page.form.submit()

    # highlight=true returns only the highlighted event
    assert {
        item.data[0].value
        for item in collection('/api/events?highlight=true').items
    } == {'Fussballturnier'}

    # highlight=false excludes the highlighted event
    assert {
        item.data[0].value
        for item in collection('/api/events?highlight=false').items
    } == all_titles - {'Fussballturnier'}

    # highlight is exposed in item data
    events = {
        item.data[0].value: item.href
        for item in collection('/api/events').items
    }
    football = collection(events['Fussballturnier']).items[0]
    assert data(football)['highlight'] is True

    gym = collection(events['Gemeinsames Turnen']).items[0]
    assert data(gym)['highlight'] is False

    # both filters can be combined
    assert not collection('/api/events?syndicate=true&highlight=true').items


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.broadcast')
@patch('onegov.websockets.integration.authenticate')
def test_view_api_search(
    authenticate: MagicMock,
    broadcast: MagicMock,
    connect: MagicMock,
    client_with_fts: Client
) -> None:

    client = client_with_fts
    client.login_admin()  # prevent rate limit

    def collection(url: str) -> Collection:
        return Collection.from_json(client.get(url).body)

    def data(item: Any) -> dict[str, Any]:
        return {x.name: x.value for x in item.data}

    def filters(item: Any) -> dict[str, Any]:
        return {x.name: x.values or x.prompt for x in item.data}

    def links(item: Any) -> dict[str, str]:
        return {x.rel: x.href for x in item.links}

    def template(item: Any) -> set[str]:
        return {x.name for x in item.template.data}

    endpoints = collection('/api')
    assert len(endpoints.queries) == 6

    # Endpoints with query hints
    assert endpoints.queries[0].rel == 'events'
    assert endpoints.queries[0].href == 'http://localhost/api/events'
    assert filters(endpoints.queries[0]).keys() == {
        'search',
        'start',
        'end',
        'locations',
        'sources',
        'syndicate',
        'highlight',
        'tags',
    }
    assert endpoints.queries[2].rel == 'news'
    assert endpoints.queries[2].href == 'http://localhost/api/news'
    assert filters(endpoints.queries[2]).keys() == {'search'}
    assert endpoints.queries[5].rel == 'topics'
    assert endpoints.queries[5].href == 'http://localhost/api/topics'
    assert filters(endpoints.queries[5]).keys() == {'search'}
    # Additional endpoints
    assert endpoints.queries[1].rel == 'forms'
    assert endpoints.queries[1].href == 'http://localhost/api/forms'
    assert not endpoints.queries[1].data
    assert endpoints.queries[3].rel == 'people'
    assert endpoints.queries[3].href == 'http://localhost/api/people'
    assert not endpoints.queries[3].data
    assert endpoints.queries[4].rel == 'resources'
    assert endpoints.queries[4].href == 'http://localhost/api/resources'
    assert not endpoints.queries[4].data

    # Events
    assert {
        item.data[0].value
        for item in collection(
            '/api/events?search=Sportanlage').items
    } == {'150 Jahre Govikon', 'Fussballturnier'}

    # News
    # TODO: Test with custom content and get rid of implicit dependency
    #       on initial content.
    assert {
        item.data[0].value
        for item in collection(
            '/api/news?search=Webseite').items
    } == {'Wir haben eine neue Webseite!'}
    assert not collection('/api/news?search=Bogus').items

    # Topics
    # TODO: Test with custom content and get rid of implicit dependency
    #       on initial content.
    assert {
        item.data[0].value
        for item in collection(
            '/api/topics?search=Kontakt').items
    } == {'Kontakt'}
    assert not collection('/api/topics?search=Bogus').items

# TODO: Test directory API


def api_item_data(item: dict[str, Any]) -> dict[str, Any]:
    return {
        entry['name']: entry['value']
        for entry in item['data']
    }


def api_items(
    client: Client,
    url: str,
    page: int | None = None,
) -> list[dict[str, Any]]:
    page_param = '' if page is None else f'?page={page}'
    response = client.get(f'{url}{page_param}')
    assert response.status_code == 200
    return response.json['collection']['items']


def test_api_people_endpoint(client: Client) -> None:
    session = client.app.session()
    session.add(Person(
        first_name='Hans',
        last_name='Muster',
        function='Mayor',
        email='hans@example.org',
        phone='0791234567',
        phone_direct='0791234568',
        organisation='Town Hall',
        academic_title='Dr.',
        profession='Politician',
        salutation='Herr',
        political_party='FDP',
    ))
    transaction.commit()

    response = client.get('/api/people')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = api_item_data(items[0])
    assert item_data['first_name'] == 'Hans'
    assert item_data['last_name'] == 'Muster'
    assert item_data['function'] == 'Mayor'
    assert item_data['email'] == 'hans@example.org'
    assert item_data['phone'] == '0791234567'
    assert item_data['phone_direct'] == '0791234568'
    assert item_data['organisation'] == 'Town Hall'
    assert item_data['academic_title'] == 'Dr.'
    assert item_data['profession'] == 'Politician'
    assert item_data['salutation'] == 'Herr'
    assert item_data['political_party'] == 'FDP'
    assert 'modified' in item_data


def test_api_forms_endpoint(client: Client) -> None:
    response = client.get('/api/forms')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) >= 1

    item_data = api_item_data(items[0])
    assert item_data['type'] == 'internal'
    assert 'title' in item_data
    assert 'text' in item_data


def test_api_forms_with_external_links(client: Client) -> None:
    session = client.app.session()
    session.add(ExternalFormLink(
        title='External Survey',
        url='https://example.org/survey',
        group='Surveys',
    ))
    transaction.commit()

    response = client.get('/api/forms')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']

    external_items = [
        item for item in items
        if any(d['name'] == 'type' and d['value'] == 'external'
               for d in item['data'])
    ]
    assert len(external_items) == 1

    ext_data = api_item_data(external_items[0])
    assert ext_data['title'] == 'External Survey'
    assert ext_data['url'] == 'https://example.org/survey'
    assert ext_data['group'] == 'Surveys'


def test_api_resources_endpoint(client: Client) -> None:
    response = client.get('/api/resources')
    assert response.status_code == 200
    data = response.json
    assert 'items' in data['collection']


def test_api_resources_with_external_links(client: Client) -> None:
    session = client.app.session()
    session.add(ExternalResourceLink(
        title='External Room',
        url='https://example.org/room',
        group='Rooms',
    ))
    transaction.commit()

    response = client.get('/api/resources')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']

    external_items = [
        item for item in items
        if any(d['name'] == 'kind' and d['value'] == 'external'
               for d in item['data'])
    ]
    assert len(external_items) == 1

    ext_data = api_item_data(external_items[0])
    assert ext_data['title'] == 'External Room'
    assert ext_data['url'] == 'https://example.org/room'


def test_api_forms_paginates_external_links_and_hides_invisible_items(
    client: Client
) -> None:
    session = client.app.session()
    forms = FormCollection(session)

    for ix in range(100):
        form = forms.definitions.add(
            f'API Form {ix:02d}',
            'E-Mail *= @@@',
            type='custom',
        )
        form.access = 'public'  # type:ignore[attr-defined]

    hidden_form = forms.definitions.add(
        'API Form Hidden',
        'E-Mail *= @@@',
        name='hidden',
        type='custom',
    )
    hidden_form.access = 'private'  # type:ignore[attr-defined]

    session.add(ExternalFormLink(
        title='API External Form',
        url='https://example.org/forms/public',
        group='API',
    ))
    hidden_id = uuid4()
    hidden_external = ExternalFormLink(
        id=hidden_id,
        title='API External Hidden',
        url='https://example.org/forms/private',
        group='API',
    )
    hidden_external.access = 'private'
    session.add(hidden_external)
    transaction.commit()

    pages = [api_items(client, '/api/forms', page) for page in range(5)]
    relevant = [
        api_item_data(item)['title']
        for items in pages
        for item in items
        if str(api_item_data(item)['title']).startswith('API ')
    ]

    assert all(len(items) <= 100 for items in pages)
    assert relevant.count('API External Form') == 1
    assert 'API External Hidden' not in relevant
    assert 'API Form Hidden' not in relevant
    assert len(set(relevant)) == 101

    client.get('/api/forms/hidden', status=404)
    client.get(f'/api/forms/{hidden_id.hex}', status=404)


def test_api_resources_paginates_external_links_and_hides_invisible_items(
    client: Client
) -> None:
    resources = client.app.libres_resources

    for ix in range(100):
        resources.add(
            title=f'API Resource {ix:02d}',
            timezone='Europe/Zurich',
            type='room',
            meta={'access': 'public'},
        )

    hidden_resource = resources.add(
        title='API Resource Hidden',
        timezone='Europe/Zurich',
        type='room',
        meta={'access': 'private'},
    )
    hidden_id = hidden_resource.id

    session = client.app.session()
    session.add(ExternalResourceLink(
        title='API External Resource',
        url='https://example.org/resources/public',
        group='API',
    ))
    hidden_external_id = uuid4()
    hidden_external = ExternalResourceLink(
        id=hidden_external_id,
        title='API External Resource Hidden',
        url='https://example.org/resources/private',
        group='API',
    )
    hidden_external.access = 'private'
    session.add(hidden_external)
    transaction.commit()

    pages = [api_items(client, '/api/resources', page) for page in range(5)]
    relevant = [
        api_item_data(item)['title']
        for items in pages
        for item in items
        if str(api_item_data(item)['title']).startswith('API ')
    ]

    assert all(len(items) <= 100 for items in pages)
    assert relevant.count('API External Resource') == 1
    assert 'API External Resource Hidden' not in relevant
    assert 'API Resource Hidden' not in relevant
    assert len(set(relevant)) == 101

    client.get(f'/api/resources/{hidden_id.hex}', status=404)
    client.get(f'/api/resources/{hidden_external_id.hex}', status=404)


def test_api_people_endpoint_hides_unpublished_entries(client: Client) -> None:
    session = client.app.session()
    session.add(Person(
        first_name='Public',
        last_name='Person',
    ))
    hidden_id = uuid4()
    hidden_person = Person(
        id=hidden_id,
        first_name='Hidden',
        last_name='Person',
        publication_start=utcnow() + timedelta(days=1),
    )
    session.add(hidden_person)
    transaction.commit()

    items = api_items(client, '/api/people')
    titles = {api_item_data(item)['title'] for item in items}

    assert 'Person Public' in titles
    assert 'Person Hidden' not in titles

    client.get(f'/api/people/{hidden_id.hex}', status=404)


def test_api_directory_content_hash(client: Client) -> None:
    session = client.app.session()
    directory: ExtendedDirectory = DirectoryCollection(
        session, type='extended'
    ).add(
        title='Clubs',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )
    directory.add(values={'name': 'Chess Club'})
    transaction.commit()

    items = api_items(client, '/api/clubs')
    assert len(items) == 1
    item_data = api_item_data(items[0])
    assert 'content_hash' in item_data
    assert item_data['content_hash'] is not None
    assert 'modified' in item_data
