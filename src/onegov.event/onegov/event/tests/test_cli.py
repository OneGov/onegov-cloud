from click.testing import CliRunner
from datetime import datetime
from onegov.core.utils import module_path
from onegov.event.cli import cli
from onegov.event.collections import EventCollection
from onegov.event.models import Event
from os import path
from pytest import mark
from transaction import commit
from unittest.mock import MagicMock
from unittest.mock import patch


def test_import_ical(cfg_path, temporary_directory):
    runner = CliRunner()

    text = '\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:Squirrel Park Visit',
        'UID:squirrel-park-visit@onegov.event',
        'DTSTART;VALUE=DATE-TIME:20150616T133000Z',
        'DTEND;VALUE=DATE-TIME:20150616T220000Z',
        'DTSTAMP;VALUE=DATE-TIME:20140101T000000Z',
        'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;UNTIL=20150616T220000Z',
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun',
        'CATEGORIES:animals',
        'LAST-MODIFIED;VALUE=DATE-TIME:20140101T000000Z',
        'LOCATION:Squirel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ])
    ical = path.join(temporary_directory, 'ical.ics')
    with open(ical, 'w') as f:
        f.write(text)

    # First import
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'import-ical', ical
    ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "1 added, 0 updated, 0 deleted" in result.output

    # Re-import
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'import-ical', ical
    ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "0 added, 0 updated, 0 deleted" in result.output

    # Clear
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'clear'
    ], 'y')
    assert result.exit_code == 0

    # Import
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'import-ical', ical
    ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "1 added, 0 updated, 0 deleted" in result.output

    # Adjust ical
    with open(ical, 'w') as f:
        f.write(text.replace('Squirel', 'Squirrel'))

    # Reimport
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'import-ical', ical
    ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "0 added, 1 updated, 0 deleted" in result.output


@mark.parametrize("xml", [
    module_path('onegov.event', 'tests/fixtures/guidle.xml'),
])
def test_import_guidle(cfg_path, temporary_directory, xml):
    runner = CliRunner()

    with open(xml) as f:
        text = f.read()
    response = MagicMock(text=text)

    # First import
    with patch('onegov.event.cli.get', return_value=response):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/foo/bar',
            'import-guidle', "'https://example.org/abcd'",
        ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "4 added, 0 updated, 0 deleted" in result.output

    # Reimport, not changed due to last_update
    with patch('onegov.event.cli.get', return_value=response):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/foo/bar',
            'import-guidle', "'https://example.org/abcd'",
        ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "0 added, 0 updated, 0 deleted" in result.output

    # Reimport, not changed due to not changed
    response.text.replace('2017-10-21', '2017-10-22')
    with patch('onegov.event.cli.get', return_value=response):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/foo/bar',
            'import-guidle', "'https://example.org/abcd'",
        ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "0 added, 0 updated, 0 deleted" in result.output

    # Clear
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'clear'
    ], 'y')
    assert result.exit_code == 0

    # Create tagmap
    tagmap = path.join(temporary_directory, 'tagmap.csv')
    with open(tagmap, 'w') as f:
        f.write("Konzert Pop / Rock / Jazz,Konzert\nSport,Sport")

    # Re-import with tagmap
    with patch('onegov.event.cli.get', return_value=response):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/foo/bar',
            'import-guidle', "'https://example.org/abcd'",
            '--tagmap', tagmap
        ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "Tags not in tagmap: \"Kulinarik\"!"
    assert "4 added, 0 updated, 0 deleted" in result.output


def test_fetch(cfg_path, session_manager):
    runner = CliRunner()

    session_manager.ensure_schema_exists('foo-baz')
    session_manager.ensure_schema_exists('foo-qux')

    def get_session(entity):
        session_manager.set_current_schema(f'foo-{entity}')
        return session_manager.session()

    for entity, title, source, tags, location in (
        ('bar', '1', None, [], ''),
        ('bar', '2', None, ['A'], None),
        ('bar', '3', None, ['A', 'B'], 'bar'),
        ('bar', '4', None, ['A', 'C'], '1234 Bar'),
        ('bar', '5', None, ['C'], 'there in 4321 baz!'),
        ('bar', '6', 'xxx', [], 'bar'),
        ('bar', '7', 'yyy', ['A', 'B'], None),
        ('baz', 'a', None, [], 'BAZ'),
        ('baz', 'b', None, ['A', 'C'], '4321 Baz'),
        ('baz', 'c', 'zzz', ['B', 'C'], 'bar'),
    ):
        EventCollection(get_session(entity)).add(
            title=title,
            start=datetime(2015, 6, 16, 9, 30),
            end=datetime(2015, 6, 16, 18, 00),
            timezone='Europe/Zurich',
            tags=tags,
            location=location,
            source=source
        )
    commit()

    assert get_session('bar').query(Event).count() == 7
    assert get_session('baz').query(Event).count() == 3
    assert get_session('qux').query(Event).count() == 0

    # No sources provided
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/qux',
        'fetch',
    ])
    assert result.exit_code != 0
    assert "Provide at least one source" in result.output

    # Bar[*] -> Qux
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/qux',
        'fetch',
        '--source', 'bar'
    ])
    assert result.exit_code == 0
    assert "5 added, 0 updated, 0 deleted" in result.output

    # Bar[B, C] -> Qux
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/qux',
        'fetch',
        '--source', 'bar',
        '--tag', 'A',
        '--tag', 'B'
    ])
    assert result.exit_code == 0
    assert "0 added, 0 updated, 2 deleted" in result.output

    # Bar[C], Baz[C] -> Qux
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/qux',
        'fetch',
        '--source', 'bar',
        '--source', 'baz',
        '--tag', 'C',
    ])
    assert result.exit_code == 0
    assert "2 added, 0 updated, 2 deleted" in result.output

    # Baz['bar'] qux['bar'] -> Bar
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'fetch',
        '--source', 'baz',
        '--source', 'qux',
        '--location', 'bar',
    ])
    assert result.exit_code == 0
    assert "0 added, 0 updated, 0 deleted" in result.output

    # Bar['baz'] -> Baz
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/baz',
        'fetch',
        '--source', 'qux',
        '--source', 'bar',
        '--location', 'baz',
    ])
    assert result.exit_code == 0
    assert "1 added, 0 updated, 0 deleted" in result.output
