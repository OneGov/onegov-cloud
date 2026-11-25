from __future__ import annotations

import pytest

from onegov.winterthur.roadwork import (
    Roadwork,
    RoadworkClient,
    RoadworkCollection,
    RoadworkConfig,
    RoadworkConnectionError,
    RoadworkError,
)


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path


# --- RoadworkConfig -----------------------------------------------------


def test_roadwork_config_parse(tmp_path: Path) -> None:
    secret = tmp_path / 'pdb.secret'
    secret.write_text(
        '# a comment\n'
        '\n'
        'HOSTNAME: pdb.example.org\n'
        'ENDPOINT: 127.0.0.1:6004\n'
        'USERNAME: user\n'
        'PASSWORD: pass\n'
        'no-colon-line\n'
        'UNKNOWN: ignored\n'
    )

    parsed = RoadworkConfig.parse(secret)
    assert parsed == {
        'hostname': 'pdb.example.org',
        'endpoint': '127.0.0.1:6004',
        'username': 'user',
        'password': 'pass',
    }


def test_roadwork_config_lookup(tmp_path: Path, monkeypatch: Any) -> None:
    secret = tmp_path / 'pdb.secret'
    secret.write_text('HOSTNAME: pdb.example.org\n')

    monkeypatch.setattr(
        RoadworkConfig, 'lookup_paths',
        classmethod(lambda cls: iter([secret]))
    )
    config = RoadworkConfig.lookup()
    assert config.hostname == 'pdb.example.org'


def test_roadwork_config_lookup_missing(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(
        RoadworkConfig, 'lookup_paths',
        classmethod(lambda cls: iter([tmp_path / 'nope']))
    )
    with pytest.raises(RoadworkError):
        RoadworkConfig.lookup()


# --- Roadwork data wrapper ----------------------------------------------


def test_roadwork_wrapper() -> None:
    work = Roadwork({
        'Id': 1,
        'ProjektBezeichnung': 'Alpha',
        'ProjektBereich': 'zone',
        'DauerVon': '2020-01-01T00:00:00+00:00',
        'DauerBis': None,
    })

    assert work.id == 1
    assert work.title == 'Alpha zone'
    assert list(work.letters) == ['a', 'z']
    assert 'Id' in work
    assert 'Missing' not in work

    # convertors turn the duration strings into datetimes
    assert work['DauerVon'].year == 2020
    assert work['DauerBis'] is None


def test_roadwork_letters_skips_non_alpha() -> None:
    work = Roadwork({
        'Id': 2,
        'ProjektBezeichnung': '1st street',
        'ProjektBereich': '',
    })
    assert list(work.letters) == []


# --- RoadworkCollection with a stubbed client ---------------------------


class StubClient:

    def __init__(
        self,
        records: list[dict[str, Any]],
        by_id_records: list[dict[str, Any]] | None = None,
    ) -> None:
        self.records = records
        self.by_id_records = by_id_records

    def get(self, url: str) -> dict[str, Any]:
        if 'Baustellen(' in url:
            return {'value': self.by_id_records or []}
        return {'value': self.records}


def _records() -> list[dict[str, Any]]:
    past = '2020-01-01T00:00:00+00:00'
    future = '2999-01-01T00:00:00+00:00'
    return [
        {
            'Id': 1, 'Internet': True,
            'ProjektBezeichnung': 'Alpha', 'ProjektBereich': '',
            'DauerVon': past, 'DauerBis': future,
            'Teilbaustellen': [{
                'TeilbaustelleId': 10,
                'DauerVon': past, 'DauerBis': future,
            }],
        },
        {
            'Id': 2, 'Internet': True,
            'ProjektBezeichnung': 'Beta', 'ProjektBereich': '',
            'DauerVon': past, 'DauerBis': future,
            'Teilbaustellen': [],
        },
        {
            'Id': 3, 'Internet': False,
            'ProjektBezeichnung': 'Hidden', 'ProjektBereich': '',
            'DauerVon': past, 'DauerBis': future,
            'Teilbaustellen': [],
        },
    ]


def test_roadwork_collection_filtering() -> None:
    client = StubClient(_records())
    collection = RoadworkCollection(client)  # type: ignore[arg-type]

    # non-internet roadwork is filtered out, results sorted by title
    works = collection.roadwork
    assert [w.title for w in works] == ['Alpha', 'Beta']

    # letters across all roadwork
    assert collection.letters == ['a', 'b']

    # query filter
    assert [w.title for w in RoadworkCollection(
        client, query='alpha').roadwork] == ['Alpha']  # type: ignore[arg-type]

    # letter filter (via by_letter)
    assert [w.title for w in collection.by_letter('b').roadwork] == ['Beta']


def test_roadwork_collection_by_id_direct() -> None:
    client = StubClient(_records(), by_id_records=[_records()[1]])
    collection = RoadworkCollection(client)  # type: ignore[arg-type]

    found = collection.by_id(2)
    assert found is not None
    assert found.title == 'Beta'


def test_roadwork_collection_by_id_section_fallback() -> None:
    # direct lookup returns nothing -> scan subsections
    client = StubClient(_records(), by_id_records=[])
    collection = RoadworkCollection(client)  # type: ignore[arg-type]

    section = collection.by_id(10)
    assert section is not None
    assert section.id == 10

    assert collection.by_id(999) is None


# --- RoadworkClient caching state machine -------------------------------


class FakeCache:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        from dogpile.cache.api import NO_VALUE
        return self.store.get(key, NO_VALUE)

    def set(self, key: str, value: Any) -> None:
        self.store[key] = value


class FakeClient(RoadworkClient):
    def __init__(self) -> None:
        super().__init__(
            cache=FakeCache(),  # type: ignore[arg-type]
            hostname='pdb.example.org',
            username='u',
            password='p',
        )
        self.response: tuple[int, Any] | Exception = (200, {'ok': True})
        self.calls = 0

    def get_uncached(self, path: str) -> tuple[int, Any]:
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_roadwork_client_caches_result() -> None:
    client = FakeClient()

    assert client.get('data') == {'ok': True}
    assert client.calls == 1

    # within lifetime the cached value is returned without a new call
    assert client.get('data') == {'ok': True}
    assert client.calls == 1


def test_roadwork_client_non_200_raises() -> None:
    client = FakeClient()
    client.response = (404, 'not found')
    with pytest.raises(RoadworkError):
        client.get('data')


def test_roadwork_client_server_error_raises_connection_error() -> None:
    client = FakeClient()
    client.response = (503, 'unavailable')
    with pytest.raises(RoadworkConnectionError):
        client.get('data')


def test_roadwork_client_connection_error() -> None:
    import pycurl
    client = FakeClient()
    client.response = pycurl.error('boom')
    with pytest.raises(RoadworkConnectionError):
        client.get('data')


def test_roadwork_client_serves_stale_within_downtime() -> None:
    from datetime import timedelta
    from sedate import utcnow

    client = FakeClient()
    assert client.get('data') == {'ok': True}

    # age the cache entry past the lifetime but within the downtime window
    entry = client.cache.store['data']  # type: ignore[attr-defined]
    entry['created'] = utcnow() - timedelta(minutes=10)

    # the backend is now down -> the stale value is served
    client.response = (503, 'unavailable')
    assert client.get('data') == {'ok': True}
