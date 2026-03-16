from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from collection_json import Collection
from freezegun import freeze_time

from onegov.town6 import TownApp
from tests.shared.client import Client


@pytest.fixture(autouse=True)
def patch_collection_json(monkeypatch: pytest.MonkeyPatch) -> None:
    # FIXME: We should probably get rid of collection_json, since it
    #        is unmaintained and doesn't follow the spec properly by
    #        raising for unknown properties, rather than ignoring them
    def Collection__init__(
            self: Any,
            href: str,
            links: Any = None,
            items: Any = None,
            queries: Any = None,
            template: Any = None,
            error: Any = None,
            version: str = '1.0',
            **extra: Any
    ) -> None:
        self.version = version
        self.href = href
        self.error = error
        self.template = template
        self.items = items
        self.links = links
        self.queries = queries

    def Query__init__(
            self: Any,
            href: str,
            rel: str,
            name: str | None = None,
            prompt: str | None = None,
            data: dict[str, str] | None = None,
            **extra: Any,
    ) -> None:
        self.href = href
        self.rel = rel
        self.name = name
        self.prompt = prompt
        self.data = data

    monkeypatch.setattr(Collection, '__init__', Collection__init__)
    monkeypatch.setattr('collection_json.Query.__init__', Query__init__)


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.broadcast')
@patch('onegov.websockets.integration.authenticate')
def test_event_api(
    authenticate: MagicMock,
    broadcast: MagicMock,
    connect: MagicMock,
    client: Client[TownApp]
) -> None:
    client.login_admin()

    def collection(url: str) -> Collection:
        return Collection.from_json(client.get(url).body)

    def data(item: Any) -> Any:
        return {x.name: x.value for x in item.data}

    def links(item: Any) -> Any:
        return {x.rel: x.href for x in item.links}

    with freeze_time('2026-02-16 15:20'):
        endpoints = collection('/api')
        assert endpoints.queries[0].rel == 'events'
        assert endpoints.queries[0].href == 'http://localhost/api/events?page=0'

        assert collection('/api/events').items

        events = {
            item.data[0].value: item.href
            for item in collection('/api/events').items
        }

        assert set(events) == {
            '150 Jahre Govikon',
            'Gemeinsames Turnen',
            'Generalversammlung',
            'Fussballturnier'
        }

        party = collection(events['150 Jahre Govikon']).items[0]
        party_data = data(party)
        assert party_data.pop('created') is not None
        assert party_data.pop('modified') is not None
        assert party_data == {
            'title': '150 Jahre Govikon',
            'description': 'Wir feiern unser 150 jähriges Bestehen.',
            'organizer': 'Govikon',
            'organizer_email': None,
            'organizer_phone': None,
            'external_event_url': None,
            'event_registration_url': None,
            'price': None,
            'tags': ['Party'],
            'start': '2026-03-22T10:00:00+00:00',
            'end': '2026-03-22T21:00:00+00:00',
            'location': 'Sportanlage',
            'coordinates': {'lat': None, 'lon': None, 'zoom': None},
        }

        assert links(party) == {
            'html': 'http://localhost/event/150-jahre-govikon-2026-03-22',
            'image': None,
            'pdf': None
        }