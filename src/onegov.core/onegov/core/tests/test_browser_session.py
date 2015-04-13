import pytest

from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from onegov.core.browser_session import BrowserSession


def test_browser_session_mangle():
    session = BrowserSession('ns', 'token', {})
    assert session.mangle('test') == 'ns:token:test'

    with pytest.raises(AssertionError):
        session.mangle('')

    with pytest.raises(AssertionError):
        session.mangle(None)


def test_browser_session_cache():
    cache = make_region().configure('dogpile.cache.memory')
    session = BrowserSession('ns', 'token', cache)

    assert not session.has('name')
    assert session.name is NO_VALUE
    assert cache.get('ns:token:name') is NO_VALUE

    session.name = 'test'
    assert session.has('name')
    assert session.name == 'test'
    assert cache.get('ns:token:name') == 'test'

    del session.name
    assert not session.has('name')
    assert session.name is NO_VALUE
    assert cache.get('ns:token:name') is NO_VALUE


def test_browser_session_cache_namespacing():
    cache = make_region().configure('dogpile.cache.memory')

    session = BrowserSession('ns', 'token', cache)
    session.name = 'test'
    assert session.name == 'test'

    session = BrowserSession('ns', 'token', cache)
    assert session.name == 'test'

    session = BrowserSession('ns', 'token2', cache)
    assert session.name is NO_VALUE

    session = BrowserSession('ns2', 'token', cache)
    assert session.name is NO_VALUE
