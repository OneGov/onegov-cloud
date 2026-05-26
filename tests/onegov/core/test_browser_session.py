from __future__ import annotations

import pytest
import transaction

from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from onegov.core import cache
from onegov.core.browser_session import BrowserSession


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

    del session.name
    assert not session.has('name')
    assert 'name' not in session

    with pytest.raises(AttributeError):
        session.name

    with pytest.raises(KeyError):
        session['name']


def test_browser_session_cache_prefix() -> None:
    cache = make_region().configure('dogpile.cache.memory')

    session = BrowserSession(cache, 'foo')  # type: ignore[arg-type]
    transaction.begin()
    session.name = 'test'
    transaction.commit()
    assert session.name == 'test'

    session = BrowserSession(cache, 'foo')  # type: ignore[arg-type]
    assert session.name == 'test'

    session = BrowserSession(cache, 'bar')  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        session.name

    session = BrowserSession(cache, 'bar')  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        session.name


def test_browser_session_data_manager(redis_url: str) -> None:
    session = BrowserSession(cache.get('sessions', 60, redis_url), 'foo')

    transaction.begin()
    session['foo'] = 'bar'
    session['bar'] = 'baz'
    assert session['foo'] == 'bar'
    assert session['bar'] == 'baz'
    assert session._pending_overrides == {'foo': 'bar', 'bar': 'baz'}
    # before the commit nothing is written to the actual cache
    assert session._cache.get('foo') is NO_VALUE
    assert session._cache.get('bar') is NO_VALUE

    # after the commit, the cache the changes have been mirrored
    transaction.commit()
    assert session['foo'] == 'bar'
    assert session['bar'] == 'baz'
    assert not session._pending_overrides
    assert session._cache.get('foo') == 'bar'
    assert session._cache.get('bar') == 'baz'

    # and we can start a new transaction
    transaction.begin()
    del session['bar']
    session['baz'] = 'foo'
    assert session['foo'] == 'bar'
    assert 'bar' not in session
    assert session['baz'] == 'foo'
    assert session._pending_overrides == {'baz': 'foo'}
    assert session._pending_deletes == {'bar'}
    assert session._cache.get('foo') == 'bar'
    assert session._cache.get('bar') == 'baz'
    assert session._cache.get('baz') is NO_VALUE

    # after an abort the session is back to how it was before
    transaction.abort()
    assert session['foo'] == 'bar'
    assert session['bar'] == 'baz'
    assert 'baz' not in session
    assert not session._pending_overrides
    assert not session._pending_deletes
    assert session._cache.get('foo') == 'bar'
    assert session._cache.get('bar') == 'baz'
    assert session._cache.get('baz') is NO_VALUE

    # flushes get deferred as well
    transaction.begin()
    session.flush()
    session['baz'] = 'foo'
    assert 'foo' not in session
    assert 'bar' not in session
    assert session['baz'] == 'foo'
    assert session._pending_overrides == {'baz': 'foo'}
    assert session._pending_flush
    assert session._cache.get('foo') == 'bar'
    assert session._cache.get('bar') == 'baz'
    assert session._cache.get('baz') is NO_VALUE

    # the commit correctly orders the operations
    transaction.commit()
    session = session  # undo mypy narrowing
    assert 'foo' not in session
    assert 'bar' not in session
    assert session['baz'] == 'foo'
    assert not session._pending_overrides
    assert not session._pending_flush
    assert session._cache.get('foo') is NO_VALUE
    assert session._cache.get('bar') is NO_VALUE
    assert session._cache.get('baz') == 'foo'

    # savepoints work too!
    transaction.begin()
    session['foo'] = 'bar'
    savepoint = transaction.savepoint()
    session['bar'] = 'baz'
    assert session['foo'] == 'bar'
    assert session['bar'] == 'baz'
    assert session['baz'] == 'foo'
    assert session._pending_overrides == {'foo': 'bar', 'bar': 'baz'}
    assert session._cache.get('foo') is NO_VALUE
    assert session._cache.get('bar') is NO_VALUE
    assert session._cache.get('baz') == 'foo'

    # rolling back the savepoint only rolls back those changes
    savepoint.rollback()
    assert session._pending_overrides == {'foo': 'bar'}
    transaction.commit()
    assert session['foo'] == 'bar'
    assert 'bar' not in session
    assert session['baz'] == 'foo'
    assert not session._pending_overrides
    assert session._cache.get('foo') == 'bar'
    assert session._cache.get('bar') is NO_VALUE
    assert session._cache.get('baz') == 'foo'


def test_browser_session_data_manager_callback(redis_url: str) -> None:
    session = BrowserSession(
        cache.get('sessions', 60, redis_url),
        'foo',
        # modifying the session within the callback is allowed
        on_dirty=lambda session, token: session.set('extra', 'foo')
    )

    transaction.begin()
    session['foo'] = 'bar'
    transaction.commit()
    assert session._cache.get('foo') == 'bar'
    assert session._cache.get('extra') == 'foo'


    on_dirty_called = False
    # aborting changes, avoids the callback being invoked
    def on_dirty(session: BrowserSession, token: str) -> None:
        nonlocal on_dirty_called
        on_dirty_called = True
        session.set('extra', 'bar')

    session = BrowserSession(
        cache.get('sessions', 60, redis_url),
        'foo',
        on_dirty=on_dirty
    )
    transaction.begin()
    session['bar'] = 'baz'
    transaction.abort()
    assert not on_dirty_called
    assert session._cache.get('foo') == 'bar'
    assert session._cache.get('extra') == 'foo'
