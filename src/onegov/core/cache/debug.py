from __future__ import annotations

import click

from contextlib import contextmanager
from onegov.core.cache.redis import RedisCacheRegion


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


WRAPPED_METHODS = (
    'get', 'get_multi', 'get_or_create', 'get_or_create_multi',
    'set', 'set_multi', 'delete', 'delete_multi',
)


@contextmanager
def analyze_cache_queries(
    report: Literal['summary', 'redundant', 'all'] = 'summary'
) -> Iterator[None]:
    """ Analyzes the redis cache round-trips executed during its context.
    Mirrors :func:`onegov.core.orm.debug.analyze_sql_queries`. There are
    three levels of information (report argument):

    * 'summary' (only show the number of round-trips)
    * 'redundant' (show summary and the keys hit more than once)
    * 'all' (show summary and every round-trip)

    Use this with a with-statement::

        with analyze_cache_queries():
            ...  # <- analyzes all cache round-trips that happen inside here

    """

    assert report in {'summary', 'redundant', 'all'}

    queries: dict[tuple[str, str], int] = {}
    originals: dict[str, Callable[..., Any]] = {}

    def record(method: str, key: Any) -> None:
        # set_multi takes a mapping, the other *_multi methods a key list
        if isinstance(key, dict):
            keys: Any = key.keys()
        elif isinstance(key, (list, tuple, set)):
            keys = key
        else:
            keys = (key,)
        for k in keys:
            entry = (method, str(k))
            if report == 'all':
                click.echo(f'> {method} {k}')
            queries[entry] = queries.get(entry, 0) + 1

    def make_wrapper(
        method: str,
        original: Callable[..., Any]
    ) -> Callable[..., Any]:

        def wrapper(
            self: RedisCacheRegion,
            key: Any,
            *args: Any,
            **kwargs: Any
        ) -> Any:
            record(f'{self.namespace}:{method}', key)
            return original(self, key, *args, **kwargs)

        return wrapper

    for method in WRAPPED_METHODS:
        original = getattr(RedisCacheRegion, method)
        originals[method] = original
        setattr(RedisCacheRegion, method, make_wrapper(method, original))

    try:
        yield
    finally:
        for method, original in originals.items():
            setattr(RedisCacheRegion, method, original)

        total = sum(queries.values())
        redundant = sum(1 for v in queries.values() if v > 1)

        if total > 10:
            total_str = click.style(str(total), 'red')
        elif total > 5:
            total_str = click.style(str(total), 'yellow')
        else:
            total_str = click.style(str(total), 'green')

        redundant_str = (
            click.style(str(redundant), 'red') if redundant else '0'
        )

        if total:
            click.echo(
                'executed {} cache round-trips, {} of which were '
                'redundant'.format(total_str, redundant_str)
            )

        if redundant and report == 'redundant':
            click.echo('The following cache keys were hit more than once:')
            for (method, key), count in queries.items():
                if count > 1:
                    click.echo(f'> {method} {key} ({count}x)')
