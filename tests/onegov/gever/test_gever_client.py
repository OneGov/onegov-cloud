from __future__ import annotations

import pytest

from onegov.gever.gever_client import GeverClientCAS
from types import SimpleNamespace


from typing import Any


def _client() -> GeverClientCAS:
    return GeverClientCAS('user', 'pass', 'https://gever.example.org')


def test_url_construction() -> None:
    client = _client()
    assert client.portal_url == 'https://gever.example.org/portal'
    assert client.login_url == 'https://gever.example.org/portal/api/login'
    assert client.ticket_url == \
        'https://gever.example.org/portal/api/cas/tickets'

    # a trailing slash on the service url is handled
    trailing = GeverClientCAS('u', 'p', 'https://gever.example.org/')
    assert trailing.portal_url == 'https://gever.example.org/portal'


def test_token_has_expired() -> None:
    client = _client()
    assert client.token_has_expired(
        SimpleNamespace(status_code=401)) is True  # type: ignore[arg-type]
    assert client.token_has_expired(
        SimpleNamespace(status_code=200)) is False  # type: ignore[arg-type]


def test_upload_file_invalid_argument() -> None:
    client = _client()
    with pytest.raises(ValueError):
        client.upload_file(b'', 'file.pdf', 'https://gever.example.org/ep')
    with pytest.raises(ValueError):
        client.upload_file(
            'not bytes',  # type: ignore[arg-type]
            'file.pdf', 'https://gever.example.org/ep')


def test_upload_file_happy_path(monkeypatch: Any) -> None:
    client = _client()
    calls: list[tuple[str, str]] = []

    def fake_request(method: str, url: str, **kwargs: Any) -> Any:
        calls.append((method, url))
        if method == 'POST':
            return SimpleNamespace(
                status_code=201,
                headers={'Location': 'https://gever.example.org/upload/1'})
        return SimpleNamespace(status_code=204, headers={})

    monkeypatch.setattr(client, 'request', fake_request)

    resp = client.upload_file(
        b'%PDF-1.4 data', 'file.pdf', 'https://gever.example.org/ep')

    # first a tus-upload POST, then a PATCH to the returned location
    assert calls[0][0] == 'POST'
    assert calls[0][1].endswith('/@tus-upload')
    assert calls[1] == ('PATCH', 'https://gever.example.org/upload/1')
    assert resp.status_code == 204


def test_upload_file_fails_early(monkeypatch: Any) -> None:
    client = _client()

    def fake_request(method: str, url: str, **kwargs: Any) -> Any:
        # POST does not return 201 -> upload aborts
        return SimpleNamespace(status_code=500, headers={})

    monkeypatch.setattr(client, 'request', fake_request)

    resp = client.upload_file(
        b'data', 'file.pdf', 'https://gever.example.org/ep')
    assert resp.status_code == 500
