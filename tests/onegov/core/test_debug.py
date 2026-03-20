from __future__ import annotations

import click

from onegov.core.orm import debug
from sqlalchemy import text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pytest
    from sqlalchemy.orm import Session


def test_analyze_simple_sql_query(
    session: Session,
    capsys: pytest.CaptureFixture[str]
) -> None:

    with debug.analyze_sql_queries('summary'):
        session.execute(text('select 1'))

    session.execute(text('select 1'))  # must not be caught

    out = click.unstyle(capsys.readouterr()[0])
    assert out == 'executed 1 queries, 0 of which were redundant\n'


def test_analyze_redundant_sql_query(
    session: Session,
    capsys: pytest.CaptureFixture[str]
) -> None:

    with debug.analyze_sql_queries('redundant'):
        session.execute(text('select 1'))
        session.execute(text('select 1'))

    out = click.unstyle(capsys.readouterr()[0])
    assert out == (
        'executed 2 queries, 1 of which were redundant\n'
        'The following queries were redundant:\n'
        '> select 1\n'
    )


def test_analyze_all_queries(
    session: Session,
    capsys: pytest.CaptureFixture[str]
) -> None:

    with debug.analyze_sql_queries('all'):
        session.execute(text('select 1'))

    out = click.unstyle(capsys.readouterr()[0])

    assert 'select 1' in out
    assert 'took 0:00:' in out
    assert 'executed 1 queries, 0 of which were redundant' in out
