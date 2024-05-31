from click.testing import CliRunner
from sedate import utcnow

from onegov.event import Event
from onegov.search.cli import cli


# FIXME
def test_search_cli_index_status(cfg_path, session):
    # add anything to the database
    event = Event(
        state='published',
        title='Test Event',
        start=utcnow(),
        end=utcnow(),
        timezone='Europe/Zurich',
        name='test-event',
    )
    session.add(event)

    q = session.query(Event)
    assert q.count() == 1

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foobar/deadbeef',
        'index-status'
    ], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'Indexing status check OK' in result.output
