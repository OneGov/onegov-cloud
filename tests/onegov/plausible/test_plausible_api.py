from __future__ import annotations

from onegov.plausible.plausible_api import PlausibleAPI


from typing import Any


def test_send_request_without_site_id() -> None:
    api = PlausibleAPI(site_id=None)
    assert api._send_request({}) == {'results': []}


def test_get_stats(monkeypatch: Any) -> None:
    api = PlausibleAPI(site_id='site')
    monkeypatch.setattr(api, '_send_request', lambda payload: {
        'results': [{'metrics': ['10', '12', '30', '1.5', '120']}]
    })

    stats = api.get_stats()
    assert stats[0] == '10'
    # the last metric (visit duration) is converted from seconds to minutes
    assert stats[-1] == '2.0'


def test_get_stats_zero_duration(monkeypatch: Any) -> None:
    api = PlausibleAPI(site_id='site')
    monkeypatch.setattr(api, '_send_request', lambda payload: {
        'results': [{'metrics': ['1', '2', '3', '1.0', 0]}]
    })
    assert api.get_stats()[-1] == '0'


def test_get_stats_empty(monkeypatch: Any) -> None:
    api = PlausibleAPI(site_id='site')
    monkeypatch.setattr(api, '_send_request', lambda payload: {'results': []})
    assert api.get_stats() == []


def test_get_top_pages(monkeypatch: Any) -> None:
    api = PlausibleAPI(site_id='site')
    monkeypatch.setattr(api, '_send_request', lambda payload: {
        'results': [
            {'dimensions': ['/home'], 'metrics': [42]},
            {'dimensions': ['/about'], 'metrics': [7]},
        ]
    })
    assert api.get_top_pages() == {'/home': 42, '/about': 7}


def test_get_top_pages_empty(monkeypatch: Any) -> None:
    api = PlausibleAPI(site_id='site')
    monkeypatch.setattr(api, '_send_request', lambda payload: {})
    assert api.get_top_pages() == {}
