from __future__ import annotations

import gc

from onegov.core import cache
from onegov.core.framework import Framework


CALL_COUNT = 0


def test_instance_lru_cache() -> None:
    count = 0

    class Adder:
        @cache.instance_lru_cache(maxsize=1)
        def add(self, x: int, y: int) -> int:
            nonlocal count
            count += 1
            return x + y

    def function() -> None:
        a = Adder()
        assert a.add(1, 2) == 3
        assert a.add(1, 3) == 4
        assert a.add(1, 2) == 3
        assert a.add(1, 2) == 3
        assert count == 3

        b = Adder()
        assert b.add(1, 2) == 3
        assert b.add(1, 3) == 4
        assert b.add(1, 2) == 3
        assert b.add(1, 2) == 3
        assert count == 6

    function()

    gc.collect()
    objects = len([obj for obj in gc.get_objects() if isinstance(obj, Adder)])
    assert objects == 0


def test_cache_key(redis_url: str) -> None:
    region = cache.get(namespace='ns', expiration_time=60, redis_url=redis_url)
    region.set('x' * 500, 'y')  # used to fail on the old memcached system


def test_redis(redis_url: str) -> None:
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/detroit')
    app.configure_application(redis_url=redis_url)
    app.cache.set('foobar', dict(foo='bar'))

    result = app.cache.get('foobar')
    assert result
    assert result['foo'] == 'bar'


def test_cache_independence(redis_url: str) -> None:
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/washington')

    app.configure_application(redis_url=redis_url)
    app.cache.set('foo', 'bar')
    assert app.cache.get('foo')

    app.set_application_id('towns/newyork')
    assert not app.cache.get('foo')

    app.namespace = 'cities'
    app.set_application_id('cities/washington')
    assert not app.cache.get('foo')

    app.namespace = 'towns'
    app.set_application_id('towns/washington')
    assert app.cache.get('foo')


def test_cache_flush(redis_url: str) -> None:
    bar = Framework()
    bar.namespace = 'foo'
    bar.set_application_id('foo/bar')
    bar.configure_application(redis_url=redis_url)
    assert bar.cache.keys() == []

    baz = Framework()
    baz.namespace = 'foo'
    baz.set_application_id('foo/baz')
    baz.configure_application(redis_url=redis_url)
    assert baz.cache.keys() == []

    assert bar.cache.keys() == []
    assert baz.cache.keys() == []

    assert bar.cache.flush() == 0
    assert baz.cache.flush() == 0

    assert bar.cache.keys() == []
    assert baz.cache.keys() == []

    bar.cache.set('moo', 'qux')
    baz.cache.set('boo', 'qux')
    assert bar.cache.keys() == [b'foo/bar:short-term:moo']
    assert baz.cache.keys() == [b'foo/baz:short-term:boo']

    assert baz.cache.flush() == 1
    assert bar.cache.keys() == [b'foo/bar:short-term:moo']
    assert baz.cache.keys() == []

    for number in range(10000):
        baz.cache.set(str(number), 'xxx')
    assert baz.cache.flush() == 10000
    assert bar.cache.keys() == [b'foo/bar:short-term:moo']
    assert baz.cache.keys() == []
