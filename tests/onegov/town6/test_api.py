from __future__ import annotations

import json
from base64 import b64encode
from collection_json import Collection  # type: ignore[import-untyped]
from tests.onegov.api.test_views import patch_collection_json  # noqa: F401
from unittest.mock import patch


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency import AgencyApp
    from tests.shared.client import Client
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
    client: Client[AgencyApp]
) -> None:

    client.login_admin()  # prevent rate limit

    def collection(url: str) -> Collection:
        return Collection.from_json(client.get(url).body)

    def data(item: Any) -> dict[str, Any]:
        return {x.name: x.value for x in item.data}

    def filters(item: Any) -> dict[str, Any]:
        return {x.name: x.prompt for x in item.data}

    def links(item: Any) -> dict[str, str]:
        return {x.rel: x.href for x in item.links}

    def template(item: Any) -> set[str]:
        return {x.name for x in item.template.data}

    endpoints = collection('/api')
    assert len(endpoints.queries) == 3

    # Endpoints with query hints
    assert endpoints.queries[0].rel == 'events'
    assert endpoints.queries[0].href == 'http://localhost/api/events?page=0'
    assert filters(endpoints.queries[0]).keys() == {
        'start',
        'end',
        'locations',
        'sources',
        'tags',
    }
    # Additional endpoints
    assert endpoints.queries[1].rel == 'news'
    assert endpoints.queries[1].href == 'http://localhost/api/news?page=0'
    assert not endpoints.queries[1].data
    assert endpoints.queries[2].rel == 'topics'
    assert endpoints.queries[2].href == 'http://localhost/api/topics?page=0'
    assert not endpoints.queries[2].data

    # Configure event filters
    settings = client.get('/event-settings')
    settings.form['event_filter_type'] = 'filters'
    settings.form.submit().follow()

    events_page = client.get('/events')
    filter_settings = events_page.click('Konfigurieren')
    filter_settings.form['definition'] = """
        Altersgruppe =
            [ ] Kind
            [ ] Jugend
            [ ] Familie
            [ ] Alter

        Highlight =
            [ ] Ja
    """
    filter_settings.form['keyword_fields'].value = 'Altersgruppe\nHighlight'
    filter_settings.form.submit().follow()

    endpoints = collection('/api')
    event_fiters = filters(endpoints.queries[0])
    assert event_fiters.keys() == {
        'start',
        'end',
        'locations',
        'sources',
        'altersgruppe',
        'highlight',
    }
    assert event_fiters['altersgruppe'] == (
        "One of 'Kind', 'Jugend', 'Familie', 'Alter'"
        " (Can be specified multiple times)"
    )
    assert event_fiters['highlight'] == "Either 'Ja' or left unspecified"

    # Configure tags and filters
    settings = client.get('/event-settings')
    settings.form['event_filter_type'] = 'tags_and_filters'
    settings.form.submit().follow()

    endpoints = collection('/api')
    assert filters(endpoints.queries[0]).keys() == {
        'start',
        'end',
        'locations',
        'sources',
        'tags',
        'altersgruppe',
        'highlight',
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

# TODO: Test directory API
