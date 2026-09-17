from __future__ import annotations

import click
import redis

from contextlib import contextmanager
from redis.client import Pipeline


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


def _decode(value: Any) -> str:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode('utf-8', 'replace')
    return str(value)


def _describe(args: tuple[Any, ...]) -> tuple[str, str]:
    # args[0] = command, args[1] = key (if any)
    command = _decode(args[0]) if args else '?'
    key = _decode(args[1]) if len(args) > 1 else ''
    return command, key


@contextmanager
def analyze_cache_queries(
    report: Literal['summary', 'redundant', 'all'] = 'summary'
) -> Iterator[None]:
    """ Analyzes the redis commands executed during its context.
    Mirrors :func:`onegov.core.orm.debug.analyze_sql_queries`. There are
    three levels of information (report argument):

    * 'summary' (only show the number of commands)
    * 'redundant' (show summary and the keys hit more than once)
    * 'all' (show summary and every command)

    Unlike hooking our :class:`RedisCacheRegion`, this counts the actual
    commands sent to redis, so cache layers that avoid a round-trip (e.g.
    the request/schema caches in front of :func:`orm_cached`) don't inflate
    the numbers. Only two methods need hooking regardless of how the dogpile
    API evolves.

    Use this with a with-statement::

        with analyze_cache_queries():
            ...  # <- analyzes all redis commands that happen inside here

    """

    assert report in {'summary', 'redundant', 'all'}

    queries: dict[str, int] = {}

    def record(command: str, key: str) -> None:
        entry = f'{command} {key}' if key else command
        if report == 'all':
            click.echo(f'> {entry}')
        queries[entry] = queries.get(entry, 0) + 1

    # StrictRedis is an alias for Redis, so this covers both; typed as Any
    # since redis-py's generic-ness varies across versions
    orig_execute_command: Any = redis.Redis.execute_command
    orig_pipeline_execute: Any = Pipeline.execute

    def execute_command(
        self: Any,
        *args: Any,
        **options: Any
    ) -> Any:
        record(*_describe(args))
        return orig_execute_command(self, *args, **options)

    def pipeline_execute(
        self: Any,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        # one round-trip of many commands; count each for key attribution
        for cmd_args, _options in self.command_stack:
            record(*_describe(cmd_args))
        return orig_pipeline_execute(self, *args, **kwargs)

    # Pipeline buffers via its own execute_command, so no double-count
    redis.Redis.execute_command = execute_command  # type: ignore[method-assign]
    Pipeline.execute = pipeline_execute  # type: ignore[method-assign]

    try:
        yield
    finally:
        redis.Redis.execute_command = orig_execute_command  # type: ignore[method-assign]
        Pipeline.execute = orig_pipeline_execute  # type: ignore[method-assign]

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
                'executed {} redis commands, {} of which were '
                'redundant'.format(total_str, redundant_str)
            )

        if redundant and report == 'redundant':
            click.echo(
                'The following redis commands were sent more than once:'
            )
            for entry, count in queries.items():
                if count > 1:
                    click.echo(f'> {entry} ({count}x)')
