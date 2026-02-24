from __future__ import annotations

import pytest

from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from onegov.core.browser_session import BrowserSession
from onegov.core import cache


def test_browser_session_mangle() -> None:
    session = BrowserSession({}, 'token')  # type: ignore[arg-type]
    assert session._cache.mangle('test') == (
        'e352b6fc45b2bc144082d507d6a51faec0bbeab5313974f7:test')

    with pytest.raises(AssertionError):
        session._cache.mangle('')

    with pytest.raises(AssertionError):
        session._cache.mangle(None)  # type: ignore[arg-type]


def test_browser_session_cache() -> None:
    cache = make_region().configure('dogpile.cache.memory')
    session = BrowserSession(cache, 'token')  # type: ignore[arg-type]
    key = 'e352b6fc45b2bc144082d507d6a51faec0bbeab5313974f7:name'

    assert not session.has('name')
    assert 'name' not in session

    with pytest.raises(AttributeError):
        session.name

    with pytest.raises(KeyError):
        session['name']

    assert cache.get(key) is NO_VALUE

    session.name = 'test'
    assert session.has('name')
    assert 'name' in session
    assert session.name == 'test'
    assert session['name'] == 'test'
    assert cache.get(key) == 'test'

    del session.name
    assert not session.has('name')
    assert 'name' not in session

    with pytest.raises(AttributeError):
        session.name

    with pytest.raises(KeyError):
        session['name']

    assert cache.get(key) is NO_VALUE


def test_browser_session_cache_prefix() -> None:
    cache = make_region().configure('dogpile.cache.memory')

    session = BrowserSession(cache, 'foo')  # type: ignore[arg-type]
    session.name = 'test'
    assert session.name == 'test'

    session = BrowserSession(cache, 'foo')  # type: ignore[arg-type]
    assert session.name == 'test'

    session = BrowserSession(cache, 'bar')  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        session.name

    session = BrowserSession(cache, 'bar')  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        session.name


def test_browser_session_count(redis_url: str) -> None:
    session = BrowserSession(cache.get('sessions', 60, redis_url), 'token')

    assert session.count() == 0
    session['foo'] = 'bar'

    assert session.count() == 1
    session['foo'] = 'baz'

    assert session.count() == 1
    del session['foo']

    assert session.count() == 0

    session['asdf'] = 'qwerty'
    assert session.count() == 1

    session.flush()
    assert session.count() == 0

    session.flush()
    assert session.count() == 0
