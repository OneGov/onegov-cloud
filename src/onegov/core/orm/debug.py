from __future__ import annotations

import click

from contextlib import contextmanager
from sedate import utcnow
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlparse import format  # type:ignore[import-untyped]


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import timedelta
    from sqlalchemy.engine import Connection
    from sqlalchemy.engine.interfaces import ExecutionContext


class Timer:
    """ A timer that works just like a stopwatch. """

    # FIXME: We should probably change this to `time.perf_counter`
    #        we probably don't care about this returning a timedelta
    #        we could always convert from seconds back to timedelta
    #        though...

    def start(self) -> None:
        self.started = utcnow()

    def stop(self) -> timedelta:
        return utcnow() - self.started


def print_query(query: bytes) -> None:
    """ Pretty prints the given query. """
    formatted = format(query.decode('utf-8'), reindent=True)
    formatted = formatted.replace('\n', '\n  ')

    click.echo('> {}'.format(formatted))


@contextmanager
def analyze_sql_queries(
    report: Literal['summary', 'redundant', 'all'] = 'summary'
) -> Iterator[None]:
    """ Analyzes the sql-queries executed during its context. There are three
    levels of information (report argument):

    * 'summary' (only show the number of queries)
    * 'redundant' (show summary and the actual redundant queries)
    * 'all' (show summary and all executed queries)

    Use this with a with_statement::

        with analyze_sql_queries():
            ... # <- analyzes all sql queries that happen inside here

    """

    assert report in {'summary', 'redundant', 'all'}

    queries = {}
    timer = Timer()

    @event.listens_for(Engine, 'before_cursor_execute')  # type:ignore[misc]
    def before_exec(
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: ExecutionContext,
        executemany: bool
    ) -> None:
        timer.start()

    @event.listens_for(Engine, 'after_cursor_execute')  # type:ignore[misc]
    def after_exec(
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: ExecutionContext,
        executemany: bool
    ) -> None:
        runtime = timer.stop()

        def handle_query(query: bytes) -> None:
            if report == 'all':
                print_query(query)

            if query not in queries:
                queries[query] = 1
            else:
                queries[query] += 1

        if isinstance(parameters, dict):
            handle_query(cursor.mogrify(statement, parameters))
        else:
            for parameter in parameters:
                handle_query(cursor.mogrify(statement, parameter))

        if report == 'all':
            click.echo('< took {}'.format(runtime))
    yield

    event.remove(Engine, 'before_cursor_execute', before_exec)
    event.remove(Engine, 'after_cursor_execute', after_exec)

    total_queries = sum(queries.values())
    redundant_queries = sum(1 for v in queries.values() if v > 1)

    if total_queries > 10:
        total_queries_str = click.style(str(total_queries), 'red')
    elif total_queries > 5:
        total_queries_str = click.style(str(total_queries), 'yellow')
    else:
        total_queries_str = click.style(str(total_queries), 'green')

    if redundant_queries:
        redundant_queries_str = click.style(str(redundant_queries), 'red')
    else:
        redundant_queries_str = '0'

    if total_queries:
        click.echo('executed {} queries, {} of which were redundant'.format(
            total_queries_str, redundant_queries_str))

    if redundant_queries and report == 'redundant':
        click.echo('The following queries were redundant:')
        for query, count in queries.items():
            if count > 1:
                print_query(query)
