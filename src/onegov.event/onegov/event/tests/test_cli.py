from click.testing import CliRunner
from onegov.core.utils import module_path
from onegov.event.cli import cli
from os import path
from pytest import mark
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
        'RRULE:FREQ=DAILY;COUNT=5;INTERVAL=1',
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
    assert "(1 added, 0 updated, 0 deleted)" in result.output

    # Re-import
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'import-ical', ical
    ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "(0 added, 0 updated, 0 deleted)" in result.output

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
    assert "(1 added, 0 updated, 0 deleted)" in result.output

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
    assert "(0 added, 1 updated, 0 deleted)" in result.output


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
    assert "(4 added, 0 updated, 0 deleted)" in result.output

    # Reimport
    with patch('onegov.event.cli.get', return_value=response):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/foo/bar',
            'import-guidle', "'https://example.org/abcd'",
        ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "(0 added, 0 updated, 0 deleted)" in result.output

    # Clear
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'clear'
    ], 'y')
    assert result.exit_code == 0

    # Import
    with patch('onegov.event.cli.get', return_value=response):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/foo/bar',
            'import-guidle', "'https://example.org/abcd'",
        ])
    assert result.exit_code == 0
    assert "Events successfully imported" in result.output
    assert "(4 added, 0 updated, 0 deleted)" in result.output

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
    assert "(0 added, 4 updated, 0 deleted)" in result.output
