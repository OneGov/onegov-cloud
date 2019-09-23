from datetime import date
from io import BytesIO
from onegov.ballot import Vote
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.models import Canton

from tests.onegov.election_day.common import create_principal


def test_import_internal_vote_1(session, import_test_datasets):

    principal = 'sg'

    vote, errors = import_test_datasets(
        'internal',
        'vote',
        principal,
        'canton',
        date_=date(2017, 5, 21),
        vote_type='simple',
        dataset_name='energiegesetz-eng',
        expats=True
    )
    assert not errors
    assert not errors
    assert vote.completed
    assert vote.ballots.count() == 1
    assert round(vote.turnout, 2) == 40.91
    assert vote.eligible_voters == 320996
    assert vote.progress == (78, 78)
    assert vote.proposal.results.count() == 78
    assert vote.proposal.yeas == 68346
    assert vote.proposal.nays == 62523
    assert vote.proposal.empty == 406
    assert vote.proposal.invalid == 52

    # Test a roundtrip
    csv = convert_list_of_dicts_to_csv(vote.export()).encode('utf-8')

    errors = import_vote_internal(
        vote,
        create_principal(principal),
        BytesIO(csv),
        'text/plain')

    assert not errors
    assert vote.completed
    assert vote.ballots.count() == 1
    assert round(vote.turnout, 2) == 40.91
    assert vote.eligible_voters == 320996
    assert vote.progress == (78, 78)
    assert vote.proposal.results.count() == 78
    assert vote.proposal.yeas == 68346
    assert vote.proposal.nays == 62523
    assert vote.proposal.empty == 406
    assert vote.proposal.invalid == 52


def test_import_internal_vote_missing_headers(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    errors = import_vote_internal(
        vote, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'status',
                    'type',
                    'entity_id',
                    'counted',
                    'nays',
                    'invalid',
                    'empty',
                    'eligible_voters',
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        (None, "Missing columns: 'yeas'")
    ]


def test_import_internal_vote_invalid_values(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    errors = import_vote_internal(
        vote, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'status',
                    'type',
                    'entity_id',
                    'counted',
                    'yeas',
                    'nays',
                    'invalid',
                    'empty',
                    'eligible_voters',
                )),
                ','.join((
                    'xxx',  # status
                    'xxx',  # type
                    'xxx',  # entity_id
                    'xxx',  # counted
                    'xxx',  # yeas
                    'xxx',  # nays
                    'xxx',  # invalid
                    'xxx',  # empty
                    'xxx',  # eligible_voters
                )),
                ','.join((
                    'unknown',  # status
                    'proposal',  # type
                    '1234',  # entity_id
                    'true',  # counted
                    '1',  # yeas
                    '1',  # nays
                    '1',  # invalid
                    '1',  # empty
                    '0',  # eligible_voters
                )),
                ','.join((
                    'unknown',  # status
                    'proposal',  # type
                    '1711',  # entity_id
                    'true',  # counted
                    '1',  # yeas
                    '1',  # nays
                    '1',  # invalid
                    '1',  # empty
                    '100',  # eligible_voters
                )),
                ','.join((
                    'unknown',  # status
                    'proposal',  # type
                    '1711',  # entity_id
                    'true',  # counted
                    '1',  # yeas
                    '1',  # nays
                    '1',  # invalid
                    '1',  # empty
                    '100',  # eligible_voters
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )

    errors = sorted(set([(e.line, e.error.interpolate()) for e in errors]))
    print(errors)
    assert errors == [
        (2, 'Invalid ballot type'),
        (2, 'Invalid integer: eligible_voters'),
        (2, 'Invalid integer: empty'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid integer: invalid'),
        (2, 'Invalid integer: nays'),
        (2, 'Invalid integer: yeas'),
        (2, 'Invalid status'),
        (3, '1234 is unknown'),
        (3, 'More cast votes than eligible voters'),
        (3, 'No eligible voters'),
        (5, '1711 was found twice')
    ]


def test_import_internal_vote_expats(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    for expats in (False, True):
        vote.expats = expats
        errors = import_vote_internal(
            vote, principal,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'status',
                        'type',
                        'entity_id',
                        'counted',
                        'yeas',
                        'nays',
                        'invalid',
                        'empty',
                        'eligible_voters',
                    )),
                    ','.join((
                        'unknown',  # status
                        'proposal',  # type
                        '9170',  # entity_id
                        'true',  # counted
                        '20',  # yeas
                        '10',  # nays
                        '0',  # invalid
                        '0',  # empty
                        '100',  # eligible_voters
                    )),
                    ','.join((
                        'unknown',  # status
                        'proposal',  # type
                        '0',  # entity_id
                        'true',  # counted
                        '20',  # yeas
                        '10',  # nays
                        '0',  # invalid
                        '0',  # empty
                        '100',  # eligible_voters
                    )),
                ))
            ).encode('utf-8')),
            'text/plain'
        )
        errors = [(e.line, e.error.interpolate()) for e in errors]
        if expats:
            assert errors == [(3, '0 was found twice')]
        else:
            assert errors == [(None, 'No data found')]

        errors = import_vote_internal(
            vote, principal,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'status',
                        'type',
                        'entity_id',
                        'counted',
                        'yeas',
                        'nays',
                        'invalid',
                        'empty',
                        'eligible_voters',
                    )),
                    ','.join((
                        'unknown',  # status
                        'proposal',  # type
                        '9170',  # entity_id
                        'true',  # counted
                        '20',  # yeas
                        '10',  # nays
                        '0',  # invalid
                        '0',  # empty
                        '100',  # eligible_voters
                    )),
                ))
            ).encode('utf-8')),
            'text/plain'
        )
        errors = [(e.line, e.error.interpolate()) for e in errors]
        result = vote.proposal.results.filter_by(entity_id=0).first()
        if expats:
            assert errors == []
            assert result.yeas == 20
        else:
            assert errors == [(None, 'No data found')]
            assert result is None


def test_import_internal_vote_temporary_results(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    errors = import_vote_internal(
        vote, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'status',
                    'type',
                    'entity_id',
                    'counted',
                    'yeas',
                    'nays',
                    'invalid',
                    'empty',
                    'eligible_voters',
                )),
                ','.join((
                    'unknown',  # status
                    'proposal',  # type
                    '1703',  # entity_id
                    'true',  # counted
                    '20',  # yeas
                    '10',  # nays
                    '1',  # invalid
                    '1',  # empty
                    '100',  # eligible_voters
                )),
                ','.join((
                    'unknown',  # status
                    'proposal',  # type
                    '1701',  # entity_id
                    'true',  # counted
                    '20',  # yeas
                    '10',  # nays
                    '1',  # invalid
                    '1',  # empty
                    '100',  # eligible_voters
                )),
                ','.join((
                    'unknown',  # status
                    'proposal',  # type
                    '1702',  # entity_id
                    'false',  # counted
                    '20',  # yeas
                    '10',  # nays
                    '1',  # invalid
                    '1',  # empty
                    '100',  # eligible_voters
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert not errors
    assert sorted(
        (v.entity_id for v in vote.proposal.results.filter_by(counted=True))
    ) == [1701, 1703]
    assert sorted(
        (v.entity_id for v in vote.proposal.results.filter_by(counted=False))
    ) == [1702, 1704, 1705, 1706, 1707, 1708, 1709, 1710, 1711]
