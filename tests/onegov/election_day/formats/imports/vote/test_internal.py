from datetime import date
from io import BytesIO
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import export_vote_internal
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.models import Canton
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import create_principal


def test_import_internal_vote_success(session, import_test_datasets):
    vote, errors = import_test_datasets(
        'internal',
        'vote',
        'sg',
        'canton',
        date_=date(2017, 5, 21),
        vote_type='simple',
        dataset_name='energiegesetz-eng',
        has_expats=True
    )
    assert not errors
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots) == 1
    assert round(vote.turnout, 2) == 40.91
    assert vote.eligible_voters == 320996
    assert vote.progress == (78, 78)
    assert len(vote.proposal.results) == 78
    assert vote.proposal.yeas == 68346
    assert vote.proposal.nays == 62523
    assert vote.proposal.empty == 406
    assert vote.proposal.invalid == 52

    # Test a roundtrip
    csv = convert_list_of_dicts_to_csv(
        export_vote_internal(vote, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH'])
    ).encode('utf-8')
    errors = import_vote_internal(
        vote,
        create_principal('sg'),
        BytesIO(csv),
        'text/plain'
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots) == 1
    assert round(vote.turnout, 2) == 40.91
    assert vote.eligible_voters == 320996
    assert vote.progress == (78, 78)
    assert len(vote.proposal.results) == 78
    assert vote.proposal.yeas == 68346
    assert vote.proposal.nays == 62523
    assert vote.proposal.empty == 406
    assert vote.proposal.invalid == 52

    # Test clearing existing results
    csv = convert_list_of_dicts_to_csv(
        export_vote_internal(vote, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH'])[:-5]
    ).replace('final', 'unknown').encode('utf-8')
    errors = import_vote_internal(
        vote,
        create_principal('sg'),
        BytesIO(csv),
        'text/plain'
    )
    assert not errors
    assert not vote.completed
    assert vote.progress == (73, 78)
    assert vote.eligible_voters < 320996
    assert vote.proposal.yeas < 68346
    assert vote.proposal.nays < 62523
    assert vote.proposal.empty < 406
    assert vote.proposal.invalid < 52

    # Test removal of existing results
    vote.domain = 'none'
    csv = convert_list_of_dicts_to_csv(
        export_vote_internal(vote, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH'])[:-8]
    ).encode('utf-8')
    errors = import_vote_internal(
        vote,
        create_principal('sg'),
        BytesIO(csv),
        'text/plain'
    )
    assert not errors
    assert vote.completed
    assert vote.progress == (70, 70)
    assert len(vote.proposal.results) == 70


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
                    'expats',
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
                    'xxx',  # expats
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
                    '0',  # expats
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
                    '100',  # expats
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
                    '',  # expats
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )

    errors = sorted(set([(e.line, e.error.interpolate()) for e in errors]))
    assert errors == [
        (2, 'Invalid ballot type'),
        (2, 'Invalid integer: eligible_voters'),
        (2, 'Invalid integer: empty'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid integer: expats'),
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

    for has_expats in (False, True):
        vote.has_expats = has_expats
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
        if has_expats:
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
        result = next(
            (r for r in vote.proposal.results if r.entity_id == 0), None
        )
        if has_expats:
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
        (v.entity_id for v in vote.proposal.results if v.counted is True)
    ) == [1701, 1703]
    assert sorted(
        (v.entity_id for v in vote.proposal.results if v.counted is False)
    ) == [1702, 1704, 1705, 1706, 1707, 1708, 1709, 1710, 1711]
    assert vote.yeas == 40
    assert vote.nays == 20
    assert vote.eligible_voters == 200
    assert vote.expats == 0
    assert vote.empty == 2
    assert vote.invalid == 2


def test_import_internal_vote_optional_columns(session):
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
                    'expats',
                )),
                ','.join((
                    'unknown',  # status
                    'proposal',  # type
                    '1701',  # entity_id
                    'true',  # counted
                    '20',  # yeas
                    '10',  # nays
                    '0',  # invalid
                    '0',  # empty
                    '100',  # eligible_voters
                    '30',  # expats
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert not errors
    result = next((r for r in vote.proposal.results if r.entity_id == 1701))
    assert result.expats == 30


def test_import_internal_vote_regional(session):

    def create_csv(results):
        lines = []
        lines.append((
            'status',
            'type',
            'entity_id',
            'counted',
            'yeas',
            'nays',
            'invalid',
            'empty',
            'eligible_voters',
            'expats',
        ))
        for entity_id, counted in results:
            lines.append((
                'unknown',  # status
                'proposal',  # type
                str(entity_id),  # entity_id
                str(counted),  # counted
                '20',  # yeas
                '10',  # nays
                '0',  # invalid
                '0',  # empty
                '100',  # eligible_voters
                '30',  # expats
            ))

        return BytesIO(
            '\n'.join(
                (','.join(column for column in line)) for line in lines
            ).encode('utf-8')
        ), 'text/plain'

    session.add(
        Vote(title='vote', domain='municipality', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()

    # ZG, municipality, too many municipalitites
    principal = Canton(canton='zg')
    vote.domain = 'municipality'
    vote.domain_segment = 'Baar'
    errors = import_vote_internal(
        vote, principal,
        *create_csv(((1701, False), (1702, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '1702 is not part of this business'
    ]

    # ZG, municipality, ok
    errors = import_vote_internal(
        vote, principal,
        *create_csv(((1701, False),))
    )
    assert not errors
    assert vote.progress == (0, 1)
