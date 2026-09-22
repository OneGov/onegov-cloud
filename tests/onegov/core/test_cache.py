import gc
import pytest

from typing import Any, Literal

from onegov.core import cache
from onegov.core.cache.debug import analyze_cache_queries
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


@pytest.mark.parametrize('report', ['summary', 'redundant', 'all'])
def test_analyze_cache_queries_report(
    report: Literal['summary', 'redundant', 'all'],
    redis_url: str,
    capsys: pytest.CaptureFixture[str]
) -> None:
    region = cache.get(
        namespace='report', expiration_time=60, redis_url=redis_url
    )

    # counts actual redis commands: SETEX + two GET on the same key
    with analyze_cache_queries(report):
        region.set('k', 1)
        region.get('a')
        region.get('a')

    out = capsys.readouterr().out

    # every mode prints the totals line
    assert 'executed 3 redis commands, 1 of which were redundant' in out
    # only 'redundant' lists the offending commands
    assert ('GET report:a (2x)' in out) == (report == 'redundant')
    # only 'all' echoes each command as it happens
    assert ('SETEX report:k' in out) == (report == 'all')


def test_analyze_cache_queries_set_multi(
    redis_url: str,
    capsys: pytest.CaptureFixture[str]
) -> None:
    region = cache.get(
        namespace='multi', expiration_time=60, redis_url=redis_url
    )

    with analyze_cache_queries('all'):
        region.set_multi({'a': 1, 'b': 2, 'c': 3})

    out = capsys.readouterr().out
    # set_multi with an expiration issues one SETEX per key
    assert 'executed 3 redis commands' in out
    assert 'SETEX multi:a' in out
    assert 'SETEX multi:b' in out
    assert 'SETEX multi:c' in out


def test_analyze_cache_queries_total_colors(
    redis_url: str,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    from onegov.core.cache import debug

    region = cache.get(
        namespace='colors', expiration_time=60, redis_url=redis_url
    )

    styled: list[tuple[str, str | None]] = []
    orig_style = debug.click.style

    def spy(text: str, fg: str | None = None, *a: Any, **k: Any) -> str:
        styled.append((text, fg))
        return orig_style(text, fg, *a, **k)

    def total_color(commands: int) -> str | None:
        styled.clear()
        monkeypatch.setattr(debug.click, 'style', spy)
        with analyze_cache_queries('summary'):
            for i in range(commands):
                region.set(str(i), i)  # one SETEX each
        monkeypatch.undo()
        # the total count is the entry styled with its own number as text
        return next(fg for text, fg in styled if text == str(commands))

    assert total_color(3) == 'green'
    assert total_color(7) == 'yellow'  # > 5
    assert total_color(12) == 'red'    # > 10


def test_with_cache_query_report(
    redis_url: str,
    capsys: pytest.CaptureFixture[str]
) -> None:
    app = Framework()
    app.configure_debug(cache_query_report='redundant')
    region = cache.get(
        namespace='wrap', expiration_time=60, redis_url=redis_url
    )

    def view() -> str:
        region.get('tags')
        region.get('tags')
        return 'ok'

    wrapped = app.with_cache_query_report(view)

    # the wrapper runs the view inside analyze_cache_queries and reports
    assert wrapped() == 'ok'
    out = capsys.readouterr().out
    assert 'redis commands' in out
    assert 'GET wrap:tags (2x)' in out


def test_analyze_cache_queries_restores_methods() -> None:
    import redis
    from redis.client import Pipeline

    before_ec = redis.Redis.execute_command
    before_pe = Pipeline.execute
    with analyze_cache_queries('summary'):
        assert redis.Redis.execute_command is not before_ec
        assert Pipeline.execute is not before_pe
    assert redis.Redis.execute_command is before_ec
    assert Pipeline.execute is before_pe
