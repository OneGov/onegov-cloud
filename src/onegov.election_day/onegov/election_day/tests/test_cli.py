import os
import transaction
import yaml

from click.testing import CliRunner
from datetime import date
from datetime import datetime
from datetime import timezone
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import Vote
from onegov.election_day.cli import cli
from onegov.election_day.models import ArchivedResult
from unittest.mock import patch


def write_config(path, postgres_dsn, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/onegov_election_day/*',
                'application': 'onegov.election_day.ElectionDayApp',
                'namespace': 'onegov_election_day',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    },
                    'sms_directory': '{}/sms'.format(
                        temporary_directory
                    ),
                    'lockfile_path': temporary_directory,
                    'd3_renderer': 'http://localhost:1337',
                },
            }
        ]
    }
    with open(path, 'w') as f:
        f.write(yaml.dump(cfg))


def write_principal(temporary_directory, principal, entity='be', params=None):
    params = params or {}
    params.update({
        'name': principal,
        'color': '#fff',
        'logo': 'canton-be.svg',
    })
    if len(entity) == 2:
        params['canton'] = entity
    else:
        params['municipality'] = entity
    path = os.path.join(
        temporary_directory,
        'file-storage/onegov_election_day-{}'.format(principal.lower())
    )
    os.makedirs(path)
    with open(os.path.join(path, 'principal.yml'), 'w') as f:
        f.write(
            yaml.dump(params, default_flow_style=False)
        )


def run_command(cfg_path, principal, commands):
    runner = CliRunner()
    return runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/onegov_election_day/{}'.format(principal),
    ] + commands)


def test_add_instance(postgres_dsn, temporary_directory, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon')

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 1
    assert "This selector may not reference an existing path" in result.output


def test_add_instance_missing_config(postgres_dsn, temporary_directory,
                                     redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "principal.yml not found" in result.output
    assert "Instance was created successfully" in result.output


def test_fetch(postgres_dsn, temporary_directory, session_manager, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)

    assert 'onegov_election_day-thun' not in session_manager.list_schemas()
    assert 'onegov_election_day-bern' not in session_manager.list_schemas()
    assert 'onegov_election_day-be' not in session_manager.list_schemas()

    write_principal(
        temporary_directory, 'BE', params={
            'fetch': {'bern': ['municipality'], 'thun': ['municipality']}
        }
    )
    write_principal(
        temporary_directory, 'Bern', entity='351', params={
            'fetch': {'be': ['federation', 'canton']}
        }
    )
    write_principal(temporary_directory, 'Thun', entity='942')

    assert run_command(cfg_path, 'be', ['add']).exit_code == 0
    assert run_command(cfg_path, 'bern', ['add']).exit_code == 0
    assert run_command(cfg_path, 'thun', ['add']).exit_code == 0

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
        session_manager.set_locale('de_CH', 'de_CH')
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

    results = (
        ('be', 'canton', 'vote-3', None, False, False),
        ('be', 'canton', 'vote-4', None, False, False),
        ('be', 'canton', 'vote-5', None, True, False),
        ('be', 'canton', 'vote-6', 'simple', False, False),
        ('be', 'canton', 'vote-7', 'simple', True, False),
        ('be', 'canton', 'vote-8', 'simple', True, True),
        ('be', 'canton', 'vote-9', 'complex', False, False),
        ('be', 'canton', 'vote-10', 'complex', True, False),
        ('be', 'canton', 'vote-11', 'complex', True, True),
    )
    for entity, domain, title, vote_type, with_id, with_result in results:
        id = '{}-{}-{}'.format(entity, domain, title)
        then = date(2010, 1, 1)

        vote = None
        if vote_type:
            vote = Vote.get_polymorphic_class(vote_type, Vote)(
                id=id, title=title, domain=domain, date=then
            )
            vote.ballots.append(Ballot(type='proposal'))
            get_session(entity).add(vote)
            get_session(entity).flush()

            if with_result:
                vote.proposal.results.append(
                    BallotResult(
                        name='Bern', entity_id=351,
                        counted=True, yeas=30, nays=10, empty=0, invalid=0
                    )
                )

            if vote_type == 'complex':
                vote.ballots.append(Ballot(type='counter-proposal'))
                vote.ballots.append(Ballot(type='tie-breaker'))

                if with_result:
                    vote.counter_proposal.results.append(
                        BallotResult(
                            name='Bern', entity_id=351,
                            counted=True, yeas=35, nays=5, empty=0, invalid=0
                        )
                    )
                    vote.tie_breaker.results.append(
                        BallotResult(
                            name='Bern', entity_id=351,
                            counted=True, yeas=0, nays=40, empty=0, invalid=0
                        )
                    )

            transaction.commit()

        get_session(entity).add(
            ArchivedResult(
                date=then,
                last_result_change=last_result_change,
                schema=get_schema(entity),
                url='{}/{}/{}'.format(entity, domain, title),
                title=title,
                domain=domain,
                name=entity,
                type='vote',
                meta={'id': id} if with_id else None
            )
        )
        get_session(entity).flush()
        transaction.commit()

    assert get_session('be').query(ArchivedResult).count() == 12
    assert get_session('bern').query(ArchivedResult).count() == 5
    assert get_session('thun').query(ArchivedResult).count() == 4

    assert run_command(cfg_path, 'be', ['fetch']).exit_code == 0

    assert get_session('be').query(ArchivedResult).count() == 12 + 4
    assert get_session('bern').query(ArchivedResult).count() == 5
    assert get_session('thun').query(ArchivedResult).count() == 4

    assert run_command(cfg_path, 'bern', ['fetch']).exit_code == 0

    assert get_session('be').query(ArchivedResult).count() == 12 + 4
    assert get_session('bern').query(ArchivedResult).count() == 5 + 12
    assert get_session('thun').query(ArchivedResult).count() == 4

    meta = {
        r.external_id: r.meta
        for r in get_session('bern').query(ArchivedResult)
        if r.meta and 'id' in r.meta
    }
    assert sorted(meta.keys()) == [
        'be-canton-vote-{}'.format(i) for i in (10, 11, 5, 7, 8)
    ]
    assert meta['be-canton-vote-8']['local'] == {
        'answer': 'accepted',
        'yeas_percentage': 75.0,
        'nays_percentage': 25.0
    }
    assert meta['be-canton-vote-11']['local'] == {
        'answer': 'counter-proposal',
        'yeas_percentage': 87.5,
        'nays_percentage': 12.5
    }

    assert run_command(cfg_path, 'thun', ['fetch']).exit_code == 0

    assert get_session('be').query(ArchivedResult).count() == 12 + 4
    assert get_session('bern').query(ArchivedResult).count() == 5 + 12
    assert get_session('thun').query(ArchivedResult).count() == 4


def test_send_sms(postgres_dsn, temporary_directory, redis_url):

    class DummyResponse(object):
        def raise_for_status(self):
            pass

        def json(self):
            return {'StatusInfo': 'OK', 'StatusCode': '1'}

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon')
    assert run_command(cfg_path, 'govikon', ['add']).exit_code == 0

    sms_path = os.path.join(
        temporary_directory, 'sms', 'onegov_election_day-govikon'
    )
    os.makedirs(sms_path)

    # no SMS yet
    send_sms = ['send-sms', 'username', 'password']
    assert run_command(cfg_path, 'govikon', send_sms).exit_code == 0

    # add a SMS
    with open(os.path.join(sms_path, '+417772211.000000'), 'w') as f:
        f.write('Fancy new results!')

    with patch(
        'onegov.election_day.utils.sms_processor.post',
        return_value=DummyResponse()
    ) as post:
        assert run_command(cfg_path, 'govikon', send_sms).exit_code == 0
        assert post.called
        assert post.call_args[0] == (
            'https://json.aspsms.com/SendSimpleTextSMS',
        )
        assert post.call_args[1] == {
            'json': {
                'MessageText': 'Fancy new results!',
                'Originator': 'OneGov',
                'Password': 'password',
                'Recipients': ['+417772211'],
                'UserName': 'username'
            }
        }


def test_generate_media(postgres_dsn, temporary_directory, session_manager,
                        redis_url):
    session_manager.set_locale('de_CH', 'de_CH')

    def add_vote(number):
        vote = Vote(
            id='vote-{}'.format(number),
            title='vote-{}'.format(number),
            domain='canton',
            date=date(2015, 6, number)
        )
        session_manager.set_current_schema('onegov_election_day-govikon')
        session = session_manager.session()
        session.add(vote)
        session.flush()

        vote.ballots.append(Ballot(type='proposal'))
        vote.proposal.results.append(
            BallotResult(
                name='x', entity_id=1, counted=True, yeas=30, nays=10
            )
        )
        transaction.commit()

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon', entity='1200')
    assert run_command(cfg_path, 'govikon', ['add']).exit_code == 0

    pdf_path = os.path.join(
        temporary_directory, 'file-storage/onegov_election_day-govikon/pdf'
    )
    svg_path = os.path.join(
        temporary_directory, 'file-storage/onegov_election_day-govikon/svg'
    )

    assert run_command(cfg_path, 'govikon', ['generate-media']).exit_code == 0
    assert os.path.exists(pdf_path)
    assert os.path.exists(svg_path)
    assert os.listdir(pdf_path) == []
    assert os.listdir(svg_path) == []

    add_vote(1)
    assert run_command(cfg_path, 'govikon', ['generate-media']).exit_code == 0
    assert len(os.listdir(pdf_path)) == 4
    assert os.listdir(svg_path) == []

    add_vote(2)
    assert run_command(cfg_path, 'govikon', ['generate-media']).exit_code == 0
    assert len(os.listdir(pdf_path)) == 8
    assert os.listdir(svg_path) == []
