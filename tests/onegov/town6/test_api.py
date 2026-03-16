from __future__ import annotations

import pytest

from typing import Any
from unittest.mock import MagicMock, patch
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

    # events
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

    # news
    with freeze_time('2026-02-16 15:25'):
        endpoints = collection('/api')
        assert endpoints.queries[1].rel == 'news'
        assert endpoints.queries[1].href == 'http://localhost/api/news?page=0'

        assert collection('/api/news').items

        directories = {
            item.data[0].value: item.href
            for item in collection('/api/news').items
        }

        assert set(directories) == {
            'Wir haben eine neue Webseite!',
        }

        article = collection(
            directories['Wir haben eine neue Webseite!']).items[0]
        article_data = data(article)
        assert article_data.pop('created') is not None
        assert article_data.pop('modified') is not None
        assert article_data.pop('text').startswith('<p>\n  Weit hinten')
        assert article_data == {
            'title': 'Wir haben eine neue Webseite!',
            'lead': 'Die neue Webseite läuft auf der Platform der OneGov '
                'Cloud.\n',
            'hashtags': [],
            'publication_start': None,
            'publication_end': None,
        }

        assert links(article) == {
            'html': 'http://localhost/news/wir-haben-eine-neue-webseite',
            'image': None,
        }

    # topics
    with freeze_time('2026-02-16 15:30'):
        endpoints = collection('/api')
        assert endpoints.queries[2].rel == 'topics'
        assert endpoints.queries[2].href == 'http://localhost/api/topics?page=0'

        assert collection('/api/topics').items

        directories = {
            item.data[0].value: item.href
            for item in collection('/api/topics').items
        }

        assert set(directories) == {
            'Kontakt',
            'Organisation',
            'Themen',
        }

        topic = collection('/api/topics').items[0]
        topic_data = data(topic)
        assert topic_data.pop('created') is not None
        assert topic_data.pop('modified') is not None
        assert topic_data.pop('text').startswith('<p>\n  Weit hinten')
        assert topic_data == {
            'title': 'Kontakt',
            'lead': 'In diesem Bereich der Website wird beschrieben wie '
                    'die Organisation zu erreichen ist.\n',
            'publication_start': None,
            'publication_end': None,
        }

        assert links(topic) == {
            'html': 'http://localhost/topics/kontakt',
            'image': None,
            'parent': None
        }

    # directories
    with freeze_time('2026-02-16 15:35'):
        endpoints = collection('/api')
        assert endpoints.queries[3].rel == 'directories'
        assert endpoints.queries[3].href == 'http://localhost/api/directories?page=0'

        assert collection('/api/directories').items

        directories = {
            item.data[0].value: item.href
            for item in collection('/api/directories').items
        }

        assert set(directories) == {
            'Board Games',
        }

        directory = collection('/api/directories').items[0]
        directory_data = data(directory)
        assert directory_data.pop('created') is not None
        assert directory_data.pop('modified') is not None
        assert directory_data == {
            'title': 'Board Games',
            'lead': None,
            'name': 'board-games',
        }

        assert links(directory) == {
            'html': 'http://localhost/directory/board-games',
            'entries': 'http://localhost/api/board-games',
        }

    # directory entries
    with freeze_time('2026-02-16 15:40'):
        endpoints = collection('/api')
        assert endpoints.queries[4].rel == 'board-games'
        assert endpoints.queries[4].href == 'http://localhost/api/board-games?page=0'

        assert collection('/api/board-games').items

        board_games = {
            item.data[0].value: item.href
            for item in collection('/api/board-games').items
        }

        assert set(board_games) == {'Catan', 'Risk'}

        entry = collection(board_games['Catan']).items[0]
        entry_data = data(entry)
        assert entry_data == {
            'title': 'Catan',
            'lead': None,
            'coordinates': {'lat': None, 'lon': None, 'zoom': None},
            'contact': None,
        }

        assert links(entry) == {
            'html': 'http://localhost/directories/board-games/catan',
        }
