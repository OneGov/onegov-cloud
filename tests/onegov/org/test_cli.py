import os
from datetime import datetime

import yaml

from click.testing import CliRunner
from transaction import commit

from onegov.chat import MessageCollection
from onegov.event import Event, EventCollection
from onegov.org.cli import cli
from onegov.ticket import TicketCollection
from onegov.user import User


def test_manage_orgs(postgres_dsn, temporary_directory, redis_url):

    cfg = {
        'applications': [
            {
                'path': '/onegov_org/*',
                'application': 'onegov.org.OrgApp',
                'namespace': 'onegov_org',
                'configuration': {
                    'dsn': postgres_dsn,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'redis_url': redis_url,
                }
            }
        ]
    }

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')

    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_org/newyork',
        'add', 'New York'
    ])

    assert result.exit_code == 0
    assert "New York was created successfully" in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_org/newyork',
        'add', 'New York'
    ])

    assert result.exit_code == 1
    assert "may not reference an existing path" in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_org/newyork', 'delete'
    ], input='y\n')

    assert result.exit_code == 0
    assert "New York was deleted successfully" in result.output


def test_fetch_with_state_and_tickets(
        cfg_path, session_manager, test_password):
    runner = CliRunner()
    local = 'baz'
    remote = 'bar'
    session_manager.ensure_schema_exists('foo-baz')
    session_manager.ensure_schema_exists('foo-bar')

    def events(entity=local):
        return get_session(entity).query(Event)

    def get_session(entity):
        session_manager.set_current_schema(f'foo-{entity}')
        return session_manager.session()

    for entity, title, source, tags, location in (
        (remote, '1', None, [], ''),
        (remote, '2', None, [], None),
    ):
        EventCollection(get_session(entity)).add(
            title=title,
            start=datetime(2015, 6, 16, 9, 30),
            end=datetime(2015, 6, 16, 18, 00),
            timezone='Europe/Zurich',
            tags=tags,
            location=location,
            source=source,
            organizer_email='triceracops@newyork.com'
        )
    commit()

    get_session(local).add(User(
        username='admin@example.org',
        password_hash=test_password,
        role='admin'
    ))
    commit()

    # test published_only, import none
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', f'/foo/{local}',
        'fetch',
        '--source', remote,
        '--create-tickets',
        '--published-only'
    ])
    assert result.exit_code == 0
    assert "0 added, 0 updated, 0 deleted" in result.output

    # Import initiated events
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', f'/foo/{local}',
        'fetch',
        '--source', remote,
        '--create-tickets',
    ])
    assert result.exit_code == 0
    assert "2 added, 0 updated, 0 deleted" in result.output
    local_event = events().filter_by(title='1').first()
    assert local_event.state == 'submitted'
    assert local_event.organizer_email == 'triceracops@newyork.com'
    assert TicketCollection(get_session(local)).query().count() == 2
    assert MessageCollection(get_session(local)).query().count() == 2
    assert TicketCollection(get_session(local)).query().first().muted is True
    collection = TicketCollection(get_session(local))
    ticket = collection.by_handler_id(local_event.id.hex)
    assert ticket.title == local_event.title
    assert ticket.handler.event == local_event
    assert ticket.handler.source == 'fetch-bar-1'
    assert ticket.handler.import_user == 'admin@example.org'
    assert ticket.state == 'open'

    # Chance the state of one ticket
    remote_event = events(remote).filter_by(title='1').first()
    remote_event.submit()
    remote_event.publish()
    commit()

    # Test not updating anything,
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/baz',
        'fetch',
        '--source', remote,
        '--create-tickets',
        '--state-transfers', 'published:withdrawn'
    ])
    assert result.exit_code == 0
    assert "0 added, 0 updated, 0 deleted" in result.output

    # Withdraw event when ticket is still open and state is initiated
    remote_event = events(remote).filter_by(title='1').first()
    remote_event.withdraw()
    commit()
    assert remote_event.state == 'withdrawn'

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/baz',
        'fetch',
        '--source', remote,
        '--create-tickets',
        '--state-transfers', 'initiated:withdrawn',
        '--state-transfers', 'submitted:withdrawn'
    ])
    assert result.exit_code == 0
    assert "0 added, 1 updated, 0 deleted" in result.output
    local_event = events(local).filter_by(title='1').first()
    assert local_event.state == 'withdrawn'
    collection = TicketCollection(get_session(local))
    ticket = collection.by_handler_id(local_event.id.hex)
    # do not touch tickets when updating state
    assert ticket.state == 'open'

    # Change state of remaining to published
    # Change the state of one ticket
    remote_event = events(remote).filter_by(title='2').first()
    remote_event.submit()
    remote_event.publish()
    commit()

    # Update local state from submitted to published
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/baz',
        'fetch',
        '--source', remote,
        '--create-tickets',
        '--state-transfers', 'submitted:published'
    ])
    assert result.exit_code == 0
    assert "0 added, 1 updated, 0 deleted" in result.output
    event = events(local).filter_by(title='2').first()
    assert event.state == 'published'

    # Delete the original event
    remote_event = events(remote).filter_by(title='2').first()
    get_session(remote).delete(remote_event)
    commit()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/baz',
        'fetch',
        '--source', remote,
        '--create-tickets',
        '--delete-orphaned-tickets'
    ])
    assert result.exit_code == 0
    assert "0 added, 0 updated, 1 deleted" in result.output
    assert TicketCollection(get_session(local)).query().count() == 1
    assert MessageCollection(get_session(local)).query().count() == 1

    # Check closing local tickets when first event is deleted
    remote_event = events(remote).filter_by(title='1').first()
    get_session(remote).delete(remote_event)
    commit()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/baz',
        'fetch',
        '--source', remote,
    ])
    assert result.exit_code == 0
    assert "0 added, 0 updated, 1 deleted" in result.output
    ticket = TicketCollection(get_session(local)).query().one()

    # for open tickets creates two ticket messages closed and opne
    messages = MessageCollection(get_session(local)).query().all()
    assert all(m.owner == 'admin@example.org' for m in messages)


def test_fetch(cfg_path, session_manager, test_password):
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
    for entity in ('bar', 'baz', 'qux'):
        get_session(entity).add(User(
            username='admin@example.org',
            password_hash=test_password,
            role='admin'
        ))
    commit()

    assert get_session('bar').query(Event).count() == 7
    assert get_session('baz').query(Event).count() == 3
    assert get_session('qux').query(Event).count() == 0
    assert get_session('bar').query(Event).first().state == 'initiated'

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
    assert get_session('qux').query(Event).first().state == 'published'


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