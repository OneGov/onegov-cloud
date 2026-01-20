from __future__ import annotations

import tarfile

from datetime import date
from io import BytesIO
from onegov.election_day.formats import import_vote_wabstic
from onegov.election_day.models import Canton
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Municipality
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import get_tar_file_path


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.types import DomainOfInfluence
    from sqlalchemy.orm import Session


def test_import_wabstic_vote(session: Session) -> None:
    # The tar file contains (modified) vote results from SG from the 12.02.2017
    # with 2 federal votes, 1 cantonal vote, 6 simple communal votes and one
    # complex communal vote

    domain: DomainOfInfluence = 'federation'
    principal_name = 'sg'

    session.add(
        Vote(title='vote', domain=domain, date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()

    tar_file = get_tar_file_path(
        domain, principal_name, 'wabstic', 'vote')

    with tarfile.open(tar_file, 'r|gz') as f:
        sgstatic_gemeinden = f.extractfile(f.next()).read()  # type: ignore
        sgstatic_geschaefte = f.extractfile(f.next()).read()  # type: ignore
        sg_gemeinden = f.extractfile(f.next()).read()  # type: ignore
        sg_geschaefte = f.extractfile(f.next()).read()  # type: ignore

    assert sgstatic_gemeinden  # we don't need this file atm
    assert sgstatic_geschaefte  # we don't need this file atm

    # Test federal results
    principal: Canton | Municipality = Canton(name=principal_name, canton='sg')
    vote.has_expats = True
    for number, yeas, completed, status in (
        ('1', 70821, True, 'final'),     # final and progress (78, 78)
        ('2', 84247, True, 'unknown'),    # unknown and progress (78, 78)
    ):
        errors = import_vote_wabstic(
            vote, principal, number, '1',
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert vote.last_result_change
        assert vote.status == status
        assert vote.progress == (78, 78)
        assert vote.completed == completed
        assert vote.yeas == yeas

    # Test cantonal results
    vote.domain = 'canton'
    vote.has_expats = True
    errors = import_vote_wabstic(
        vote, principal, '3', '1',
        BytesIO(sg_geschaefte), 'text/plain',
        BytesIO(sg_gemeinden), 'text/plain'
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots[0].results) == 78
    assert vote.yeas == 57653

    # Test communal results
    vote.domain = 'municipality'
    vote.has_expats = False
    for district, number, entity_id, yeas in (
        ('3', '1', 3204, 1871),
        ('43', '1', 3292, 743),
        ('66', '1', 3352, 1167),
        ('68', '1', 3374, 189),
        ('68', '2', 3374, 337),
        ('69', '1', 3375, 365),
    ):
        principal = Municipality(
            name=str(entity_id), municipality=str(entity_id),
            canton='sg', canton_name='Kanton St.Gallen'
        )
        errors = import_vote_wabstic(
            vote, principal, number, district,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert vote.last_result_change
        assert vote.counted
        assert vote.status == 'unknown'
        assert vote.completed
        assert vote.ballots[0].results[0].yeas == yeas

    # Test communal results (missing)
    for district, number, entity_id, domain in (
        ('3', '1', 3204, 'federation'),  # domain missing
        ('300', '1', 3204, 'municipality'),  # district missing
        ('3', '5', 3204, 'municipality'),  # number missing
    ):
        vote.domain = domain
        principal = Municipality(
            name=str(entity_id), municipality=str(entity_id),
            canton='sg', canton_name='Kanton St.Gallen'
        )
        errors = import_vote_wabstic(
            vote, principal, number, district,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        # undo mypy narrowing
        vote = vote
        assert vote.last_result_change
        assert not vote.completed
        assert not vote.ballots[0].results[0].counted

    # Test complex vote
    session.add(
        ComplexVote(
            title='vote', domain='municipality', date=date(2017, 2, 12)
        )
    )
    session.flush()
    vote = session.query(ComplexVote).one()
    principal = Municipality(
        name=str(3402), municipality=str(3402),
        canton='sg', canton_name='Kanton St.Gallen'
    )
    errors = import_vote_wabstic(
        vote, principal, '1', '83',
        BytesIO(sg_geschaefte), 'text/plain',
        BytesIO(sg_gemeinden), 'text/plain'
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots) == 3
    assert vote.proposal.yeas == 1596
    assert vote.counter_proposal.yeas == 0
    assert vote.tie_breaker.yeas == 0


def test_import_wabstic_vote_missing_headers(session: Session) -> None:
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    errors = import_vote_wabstic(
        vote, principal, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Art',
                    'SortGeschaeft',
                )),
            ))
        ).encode('utf-8')),
        'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                    'StmUngueltig',
                    'StmLeer',
                    'StmHGJa',
                    'StmHGNein',
                    'StmHGOhneAw',
                    'StmN1Ja',
                    'StmN1Nein',
                    'StmN1OhneAw',
                    'StmN2Ja',
                    'StmN2Nein',
                    'StmN2OhneAw',
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        ('sg_geschaefte', "Missing columns: 'sortwahlkreis'"
         ),
        ('sg_gemeinden', "Missing columns: 'art, sperrung'")
    ]


def test_import_wabstic_vote_invalid_values(session: Session) -> None:
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    raw_errors = import_vote_wabstic(
        vote, principal, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Art',
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                    'AnzGdePendent'
                )),
                ','.join((
                    'Eidg',
                    '0',
                    '0',
                    '4',
                    '2'
                )),
            ))
        ).encode('utf-8')),
        'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Art',
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'Sperrung',
                    'Stimmberechtigte',
                    'StmUngueltig',
                    'StmLeer',
                    'StmHGJa',
                    'StmHGNein',
                    'StmHGOhneAw',
                    'StmN1Ja',
                    'StmN1Nein',
                    'StmN1OhneAw',
                    'StmN2Ja',
                    'StmN2Nein',
                    'StmN2OhneAw',
                )),
                ','.join((
                    'Eidg',
                    '0',
                    '0',
                    '100',  # 'BfsNrGemeinde',
                    'xxx',  # 'Sperrung',
                    'aaa',  # 'Stimmberechtigte',
                    'bbb',  # 'StmUngueltig',
                    'bab',  # 'StmLeer',
                    'ccc',  # 'StmHGJa',
                    'ddd',  # 'StmHGNein',
                    'eee',  # 'StmHGOhneAw',
                    'fff',  # 'StmN1Ja',
                    'ggg',  # 'StmN1Nein',
                    'hhh',  # 'StmN1OhneAw',
                    'iii',  # 'StmN2Ja',
                    'jjj',  # 'StmN2Nein',
                    'kkk',  # 'StmN2OhneAw',
                )),
                ','.join((
                    'Eidg',
                    '0',
                    '0',
                    'xxx',  # 'BfsNrGemeinde',
                    'xxx',  # 'Sperrung',
                    'aaa',  # 'Stimmberechtigte',
                    'bbb',  # 'StmUngueltig',
                    'bab',  # 'StmLeer',
                    'ccc',  # 'StmHGJa',
                    'ddd',  # 'StmHGNein',
                    'eee',  # 'StmHGOhneAw',
                    'fff',  # 'StmN1Ja',
                    'ggg',  # 'StmN1Nein',
                    'hhh',  # 'StmN1OhneAw',
                    'iii',  # 'StmN2Ja',
                    'jjj',  # 'StmN2Nein',
                    'kkk',  # 'StmN2OhneAw',
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    errors = sorted(
        (e.filename, e.line, e.error.interpolate()) for e in raw_errors  # type: ignore[attr-defined]
    )
    assert errors == [
        ('sg_gemeinden', 2, '100 is unknown'),
        ('sg_gemeinden', 2, 'Could not read the empty votes'),
        ('sg_gemeinden', 2, 'Invalid integer: stimmberechtigte'),
        ('sg_gemeinden', 2, 'Invalid integer: stmhgja'),
        ('sg_gemeinden', 2, 'Invalid integer: stmhgnein'),
        ('sg_gemeinden', 2, 'Invalid integer: stmungueltig'),
        ('sg_gemeinden', 2, 'Invalid values'),
        ('sg_gemeinden', 3, 'Could not read the empty votes'),
        ('sg_gemeinden', 3, 'Invalid integer: bfsnrgemeinde'),
        ('sg_gemeinden', 3, 'Invalid integer: stimmberechtigte'),
        ('sg_gemeinden', 3, 'Invalid integer: stmhgja'),
        ('sg_gemeinden', 3, 'Invalid integer: stmhgnein'),
        ('sg_gemeinden', 3, 'Invalid integer: stmungueltig'),
        ('sg_gemeinden', 3, 'Invalid values'),
    ]


def test_import_wabstic_vote_expats(session: Session) -> None:
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    for has_expats in (False, True):
        for entity_id in ('9170', '0'):
            vote.has_expats = has_expats
            errors = import_vote_wabstic(
                vote, principal, '0', '0',
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'Art',
                            'SortWahlkreis',
                            'SortGeschaeft',
                            'Ausmittlungsstand',
                            'AnzGdePendent'
                        )),
                        ','.join((
                            'Eidg',
                            '0',
                            '0',
                            '0',
                            '1'
                        )),
                    ))
                ).encode('utf-8')),
                'text/plain',
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'Art',
                            'SortWahlkreis',
                            'SortGeschaeft',
                            'BfsNrGemeinde',
                            'Sperrung',
                            'Stimmberechtigte',
                            'StmUngueltig',
                            'StmLeer',
                            'StmHGJa',
                            'StmHGNein',
                            'StmHGOhneAw',
                            'StmN1Ja',
                            'StmN1Nein',
                            'StmN1OhneAw',
                            'StmN2Ja',
                            'StmN2Nein',
                            'StmN2OhneAw',
                        )),
                        ','.join((
                            'Eidg',
                            '0',
                            '0',
                            entity_id,  # 'BfsNrGemeinde',
                            '2000',  # 'Sperrung',
                            '100',  # 'Stimmberechtigte',
                            '0',  # 'StmUngueltig',
                            '1',  # 'StmLeer',
                            '',  # 'StmHGJa',
                            '',  # 'StmHGNein',
                            '',  # 'StmHGOhneAw',
                            '',  # 'StmN1Ja',
                            '',  # 'StmN1Nein',
                            '',  # 'StmN1OhneAw',
                            '',  # 'StmN2Ja',
                            '',  # 'StmN2Nein',
                            '',  # 'StmN2OhneAw',
                        ))
                    ))
                ).encode('utf-8')),
                'text/plain'
            )
            assert not errors

            result = next(
                (r for r in vote.proposal.results if r.entity_id == 0), None
            )
            if has_expats:
                assert result is not None
                assert result.empty == 1
            else:
                assert result is None


def test_import_wabstic_vote_temporary_results(session: Session) -> None:
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    errors = import_vote_wabstic(
        vote, principal, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Art',
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                    'AnzGdePendent'
                )),
                ','.join((
                    'Eidg',
                    '0',
                    '0',
                    '0',
                    '1'
                )),
            ))
        ).encode('utf-8')),
        'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Art',
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'Sperrung',
                    'Stimmberechtigte',
                    'StmUngueltig',
                    'StmLeer',
                    'StmHGJa',
                    'StmHGNein',
                    'StmHGOhneAw',
                    'StmN1Ja',
                    'StmN1Nein',
                    'StmN1OhneAw',
                    'StmN2Ja',
                    'StmN2Nein',
                    'StmN2OhneAw',
                )),
                ','.join((
                    'Eidg',
                    '0',
                    '0',
                    '3203',  # 'BfsNrGemeinde',
                    '2000',  # 'Sperrung',
                    '100',  # 'Stimmberechtigte',
                    '0',  # 'StmUngueltig',
                    '1',  # 'StmLeer',
                    '',  # 'StmHGJa',
                    '',  # 'StmHGNein',
                    '',  # 'StmHGOhneAw',
                    '',  # 'StmN1Ja',
                    '',  # 'StmN1Nein',
                    '',  # 'StmN1OhneAw',
                    '',  # 'StmN2Ja',
                    '',  # 'StmN2Nein',
                    '',  # 'StmN2OhneAw',
                ))
            ))
        ).encode('utf-8')),
        'text/plain'
    )

    assert not errors

    # 1 Present, 76 Missing
    assert vote.progress == (1, 77)


def test_import_wabstic_vote_regional(session: Session) -> None:

    def create_csv(
        results: tuple[int, ...]
    ) -> tuple[BytesIO, str, BytesIO, str]:
        lines = [
            (
                'Art',
                'SortWahlkreis',
                'SortGeschaeft',
                'BfsNrGemeinde',
                'Sperrung',
                'Stimmberechtigte',
                'StmUngueltig',
                'StmLeer',
                'StmHGJa',
                'StmHGNein',
                'StmHGOhneAw',
                'StmN1Ja',
                'StmN1Nein',
                'StmN1OhneAw',
                'StmN2Ja',
                'StmN2Nein',
                'StmN2OhneAw',
            ),
            *(
                (
                    'Gde',
                    '0',
                    '0',
                    str(entity_id),  # 'BfsNrGemeinde',
                    '2000',  # 'Sperrung',
                    '100',  # 'Stimmberechtigte',
                    '0',  # 'StmUngueltig',
                    '1',  # 'StmLeer',
                    '',  # 'StmHGJa',
                    '',  # 'StmHGNein',
                    '',  # 'StmHGOhneAw',
                    '',  # 'StmN1Ja',
                    '',  # 'StmN1Nein',
                    '',  # 'StmN1OhneAw',
                    '',  # 'StmN2Ja',
                    '',  # 'StmN2Nein',
                    '',  # 'StmN2OhneAw',
                ) for entity_id in results
            )
        ]

        return (
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Art',
                        'SortWahlkreis',
                        'SortGeschaeft',
                        'Ausmittlungsstand',
                        'AnzGdePendent'
                    )),
                    ','.join((
                        'Gde',
                        '0',
                        '0',
                        '0',
                        '1'
                    )),
                ))
            ).encode('utf-8')),
            'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(column for column in line)) for line in lines
                ).encode('utf-8')
            ),
            'text/plain'
        )

    session.add(
        Vote(title='vote', domain='municipality', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()

    # ZG, municipality, too many municipalitites
    principal = Canton(canton='zg')
    vote.domain = 'municipality'
    vote.domain_segment = 'Baar'
    errors = import_vote_wabstic(
        vote, principal, '0', '0',
        *create_csv((1701, 1702))
    )
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '1702 is not part of this business'
    ]

    # ZG, municipality, ok
    errors = import_vote_wabstic(
        vote, principal, '0', '0',
        *create_csv((1701,))
    )
    assert not errors
    assert vote.progress == (1, 1)
