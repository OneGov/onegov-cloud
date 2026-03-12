from __future__ import annotations

from click.testing import CliRunner
from onegov.event import Event
from onegov.search.cli import cli
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager


def test_search_cli_index_status(
    cfg_path: str,
    session_manager: SessionManager
) -> None:
    # add anything to the database
    event = Event(
        state='published',
        title='Test Event',
        start=utcnow(),
        end=utcnow(),
        timezone='Europe/Zurich',
        name='test-event',
    )
    session = session_manager.session()
    session.add(event)

    q = session.query(Event)
    assert q.count() == 1

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'index-status'
    ], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'Indexing status check OK' in result.output
