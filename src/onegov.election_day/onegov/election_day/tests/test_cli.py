import os
import transaction
import yaml

from click.testing import CliRunner
from datetime import date, datetime, timezone
from onegov.election_day.cli import cli
from onegov.election_day.models import ArchivedResult


def test_add_instance(postgres_dsn, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/onegov_election_day/*',
                'application': 'onegov.election_day.ElectionDayApp',
                'namespace': 'onegov_election_day',
                'configuration': {
                    'dsn': postgres_dsn,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    }
                },
            }
        ]
    }
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    principal = {
        'name': 'Govikon',
        'canton': 'be',
        'color': '#fff',
        'logo': 'canton-be.svg',
    }
    principal_path = os.path.join(
        temporary_directory, 'file-storage/onegov_election_day-govikon'
    )
    os.makedirs(principal_path)
    with open(os.path.join(principal_path, 'principal.yml'), 'w') as f:
        f.write(yaml.dump(principal, default_flow_style=False))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/govikon',
        'add',
    ])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/govikon',
        'add',
    ])
    assert result.exit_code == 1
    assert "This selector may not reference an existing path" in result.output


def test_add_instance_missing_config(postgres_dsn, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/onegov_election_day/*',
                'application': 'onegov.election_day.ElectionDayApp',
                'namespace': 'onegov_election_day',
                'configuration': {
                    'dsn': postgres_dsn,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    }
                },
            }
        ]
    }

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/govikon',
        'add',
    ])
    assert result.exit_code == 0
    assert "principal.yml not found" in result.output
    assert "Instance was created successfully" in result.output


def test_fetch(postgres_dsn, temporary_directory, session_manager):

    runner = CliRunner()

    cfg = {
        'applications': [
            {
                'path': '/onegov_election_day/*',
                'application': 'onegov.election_day.ElectionDayApp',
                'namespace': 'onegov_election_day',
                'configuration': {
                    'dsn': postgres_dsn,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    }
                },
            }
        ]
    }
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    assert 'onegov_election_day-thun' not in session_manager.list_schemas()
    assert 'onegov_election_day-bern' not in session_manager.list_schemas()
    assert 'onegov_election_day-be' not in session_manager.list_schemas()

    principals = {
        'be': {
            'name': 'Kanton Bern',
            'canton': 'be',
            'color': '#fff',
            'logo': 'canton-be.svg',
            'fetch': {
                'bern': ['municipality'],
                'thun': ['municipality']
            }
        },
        'bern': {
            'name': 'Stadt Bern',
            'municipality': '351',
            'color': '#fff',
            'logo': 'municipality-351.svg',
            'fetch': {
                'be': ['federation', 'canton'],
            }
        },
        'thun': {
            'name': 'Stadt Thun',
            'municipality': '942',
            'color': '#fff',
            'logo': 'municipality-942.svg',
            'fetch': {}
        }
    }
    for principal in principals:
        principal_path = os.path.join(
            temporary_directory,
            'file-storage/onegov_election_day-{}'.format(principal)
        )
        os.makedirs(principal_path)
        with open(os.path.join(principal_path, 'principal.yml'), 'w') as f:
            f.write(yaml.dump(principals[principal], default_flow_style=False))

        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/onegov_election_day/{}'.format(principal),
            'add',
        ])
        assert result.exit_code == 0
        assert "Instance was created successfully" in result.output

    assert 'onegov_election_day-thun' in session_manager.list_schemas()
    assert 'onegov_election_day-bern' in session_manager.list_schemas()
    assert 'onegov_election_day-be' in session_manager.list_schemas()

    last_result_change = datetime(2010, 1, 1, 0, 0, tzinfo=timezone.utc)

    results = (
        ('be', 'canton', 'vote-1'),
        ('be', 'canton', 'vote-2'),
        ('be', 'federation', 'vote'),
        ('bern', 'federation', 'vote'),
        ('bern', 'canton', 'vote-1'),
        ('bern', 'canton', 'vote-2'),
        ('bern', 'municipality', 'vote-1'),
        ('bern', 'municipality', 'vote-2'),
        ('thun', 'canton', 'vote-1'),
        ('thun', 'canton', 'vote-2'),
        ('thun', 'municipality', 'vote-1'),
        ('thun', 'municipality', 'vote-2'),
    )

    def get_schema(entity):
        return 'onegov_election_day-{}'.format(entity)

    def get_session(entity):
        session_manager.set_current_schema(get_schema(entity))
        return session_manager.session()

    for entity, domain, title in results:
        get_session(entity).add(
            ArchivedResult(
                date=date(2010, 1, 1),
                last_result_change=last_result_change,
                schema=get_schema(entity),
                url='{}/{}/{}'.format(entity, domain, title),
                title=title,
                domain=domain,
                name=entity,
                type='vote',
            )
        )
        get_session(entity).flush()
        transaction.commit()

    assert get_session('be').query(ArchivedResult).count() == 3
    assert get_session('bern').query(ArchivedResult).count() == 5
    assert get_session('thun').query(ArchivedResult).count() == 4

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/be',
        'fetch',
    ])
    assert result.exit_code == 0

    assert get_session('be').query(ArchivedResult).count() == 3 + 4
    assert get_session('bern').query(ArchivedResult).count() == 5
    assert get_session('thun').query(ArchivedResult).count() == 4

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/bern',
        'fetch',
    ])
    assert result.exit_code == 0

    assert get_session('be').query(ArchivedResult).count() == 3 + 4
    assert get_session('bern').query(ArchivedResult).count() == 5 + 3
    assert get_session('thun').query(ArchivedResult).count() == 4

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/thun',
        'fetch',
    ])
    assert result.exit_code == 0

    assert get_session('be').query(ArchivedResult).count() == 3 + 4
    assert get_session('bern').query(ArchivedResult).count() == 5 + 3
    assert get_session('thun').query(ArchivedResult).count() == 4
