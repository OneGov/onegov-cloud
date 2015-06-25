import click

from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlparse import format


class Timer(object):
    """ A timer that works just like a stopwatch. """

    def start(self):
        self.started = datetime.utcnow()

    def stop(self):
        return datetime.utcnow() - self.started


def print_query(query):
    """ Pretty prints the given query. """
    formatted = format(query.decode('utf-8'), reindent=True)
    formatted = formatted.replace('\n', '\n  ')

    print('> {}'.format(formatted))


@contextmanager
def analyze_sql_queries(report='summary'):
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

    @event.listens_for(Engine, 'before_cursor_execute')
    def before_exec(conn, cursor, statement, parameters, context, executemany):
        timer.start()

    @event.listens_for(Engine, 'after_cursor_execute')
    def after_exec(conn, cursor, statement, parameters, context, executemany):
        runtime = timer.stop()

        def handle_query(query):
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
            print('< took {}'.format(runtime))
    yield

    event.remove(Engine, 'before_cursor_execute', before_exec)
    event.remove(Engine, 'after_cursor_execute', after_exec)

    total_queries = sum(queries.values())
    redundant_queries = sum(1 for v in queries.values() if v > 1)

    if total_queries > 10:
        total_queries = click.style(str(total_queries), 'red')
    elif total_queries > 5:
        total_queries = click.style(str(total_queries), 'yellow')
    else:
        total_queries = click.style(str(total_queries), 'green')

    if redundant_queries:
        redundant_queries = click.style(str(redundant_queries), 'red')

    if total_queries != '0':
        print("executed {} queries, {} of which were redundant".format(
            total_queries, redundant_queries))

    if redundant_queries and report == 'redundant':
        print("The following queries were redundant:")
        for query, count in queries.items():
            if count > 1:
                print_query(query)
