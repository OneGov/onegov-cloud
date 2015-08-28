import click

from onegov.core.orm import debug


def test_analyze_simple_sql_query(session, capsys):

    with debug.analyze_sql_queries('summary'):
        session.execute('select 1')

    session.execute('select 1')  # must not be caught

    out = click.unstyle(capsys.readouterr()[0])
    assert out == 'executed 1 queries, 0 of which were redundant\n'


def test_analyze_redundant_sql_query(session, capsys):

    with debug.analyze_sql_queries('redundant'):
        session.execute('select 1')
        session.execute('select 1')

    out = click.unstyle(capsys.readouterr()[0])
    assert out == (
        'executed 2 queries, 1 of which were redundant\n'
        'The following queries were redundant:\n'
        '> select 1\n'
    )


def test_analyze_all_queries(session, capsys):

    with debug.analyze_sql_queries('all'):
        session.execute('select 1')

    out = click.unstyle(capsys.readouterr()[0])

    assert 'select 1' in out
    assert 'took 0:00:' in out
    assert 'executed 1 queries, 0 of which were redundant' in out
