from __future__ import annotations

import pycurl

from dogpile.cache.api import NO_VALUE

from onegov.winterthur.roadwork import RoadworkClient, RoadworkConfig


class DummyCache:

    def __init__(self) -> None:
        self.storage: dict[str, object] = {}

    def get(self, key: str) -> object:
        return self.storage.get(key, NO_VALUE)

    def set(self, key: str, value: object) -> None:
        self.storage[key] = value


def test_roadwork_client_uses_example_data() -> None:
    client = RoadworkClient(
        cache=DummyCache(),
        hostname='',
        username='',
        password='',
        endpoint=None
    )

    payload = client.get('odata/Baustellen')

    assert payload['value'][0]['ProjektBezeichnung'] == 'Baustelle Hauptstrasse'
    assert payload['value'][0]['Teilbaustellen'][0]['TeilbaustelleId'] == 456


def test_lookup_falls_back_to_example_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        RoadworkConfig,
        'lookup_paths',
        classmethod(lambda cls: iter(()))
    )

    config = RoadworkConfig.lookup()

    assert config.hostname is None
    assert config.endpoint is None
    assert config.username is None
    assert config.password is None


def test_roadwork_client_uses_example_data_on_connection_error() -> None:
    client = RoadworkClient(
        cache=DummyCache(),
        hostname='',
        username='',
        password='',
        endpoint=None
    )

    def fail(_path: str) -> tuple[int, object]:
        raise pycurl.error('boom')

    client.get_uncached = fail  # type: ignore[assignment]

    payload = client.get('odata/Baustellen')

    assert payload['value'][0]['ProjektBezeichnung'] == 'Baustelle Hauptstrasse'


def test_roadwork_client_uses_example_data_for_query_string_paths() -> None:
    client = RoadworkClient(
        cache=DummyCache(),
        hostname='',
        username='',
        password='',
        endpoint=None
    )

    payload = client.get('odata/Baustellen?addGisLink=False&$filter=DauerVon%20le%202026-08-03')

    assert payload['value'][0]['ProjektBezeichnung'] == 'Baustelle Hauptstrasse'
