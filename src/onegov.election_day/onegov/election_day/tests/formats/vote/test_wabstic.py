import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Vote
from onegov.ballot import ComplexVote
from onegov.core.utils import module_path
from onegov.election_day.formats import import_vote_wabstic
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabstic_vote.tar.gz'),
])
def test_import_wabstic_vote(session, tar_file):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()

    # The tar file contains (modified) vote results from SG from the 12.02.2017
    # with 2 federal votes, 1 cantonal vote, 6 simple communal votes and one
    # complex communal vote
    with tarfile.open(tar_file, 'r|gz') as f:
        sgstatic_gemeinden = f.extractfile(f.next()).read()
        sgstatic_geschaefte = f.extractfile(f.next()).read()
        sg_gemeinden = f.extractfile(f.next()).read()
        sg_geschaefte = f.extractfile(f.next()).read()

    assert sgstatic_gemeinden  # we don't need this file atm
    assert sgstatic_geschaefte  # we don't need this file atm

    # Test federal results
    principal = Canton(name='sg', canton='sg')
    entities = principal.entities.get(vote.date.year, {})
    for number, yeas, completed in (
        ('1', 70821, True),
        ('2', 84247, False),
    ):
        errors = import_vote_wabstic(
            vote, entities, '1', number,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert vote.completed == completed
        assert vote.ballots.one().results.count() == 78
        assert vote.yeas == yeas

    # Test cantonal results
    vote.domain = 'canton'
    errors = import_vote_wabstic(
        vote, entities, '1', '3',
        BytesIO(sg_geschaefte), 'text/plain',
        BytesIO(sg_gemeinden), 'text/plain'
    )
    assert not errors
    assert vote.completed
    assert vote.ballots.one().results.count() == 78
    assert vote.yeas == 57653

    # Test communal results
    vote.domain = 'municipality'
    for district, number, entity_id, yeas in (
        ('3', '1', 3204, 1871),
        ('43', '1', 3292, 743),
        ('66', '1', 3352, 1167),
        ('68', '1', 3374, 189),
        ('68', '2', 3374, 337),
        ('69', '1', 3375, 365),
    ):
        principal = Municipality(name=str(entity_id), municipality=entity_id)
        entities = principal.entities.get(vote.date.year, {})
        errors = import_vote_wabstic(
            vote, entities, district, number,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert vote.completed
        assert vote.ballots.one().results.one().yeas == yeas

    # Test communal results (missing)
    for district, number, entity_id, domain in (
        ('3', '1', 3204, 'federation'),  # domain missing
        ('300', '1', 3204, 'municipality'),  # district missing
        ('3', '5', 3204, 'municipality'),  # number missing
    ):
        vote.domain = domain
        principal = Municipality(name=str(entity_id), municipality=entity_id)
        entities = principal.entities.get(vote.date.year, {})
        errors = import_vote_wabstic(
            vote, entities, district, number,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert not vote.completed
        assert not vote.ballots.one().results.one().counted

    # Test complex vote
    session.add(
        ComplexVote(
            title='vote', domain='municipality', date=date(2017, 2, 12)
        )
    )
    session.flush()
    vote = session.query(ComplexVote).one()
    principal = Municipality(name=str(3402), municipality=3402)
    entities = principal.entities.get(vote.date.year, {})
    errors = import_vote_wabstic(
        vote, entities, '83', '1',
        BytesIO(sg_geschaefte), 'text/plain',
        BytesIO(sg_gemeinden), 'text/plain'
    )
    assert not errors
    assert vote.completed
    assert vote.ballots.count() == 3
    assert vote.proposal.yeas == 1596
    assert vote.counter_proposal.yeas == 0
    assert vote.tie_breaker.yeas == 0


def test_import_wabstic_vote_missing_headers(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')
    entities = principal.entities.get(vote.date.year, {})

    errors = import_vote_wabstic(
        vote, entities, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Art',
                    'SortWahlkreis',
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
                    'SortGemeinde',
                    'SortGemeindeSub',
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
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        ('sg_geschaefte', "Missing columns: 'ausmittlungsstand'"),
        ('sg_gemeinden', "Missing columns: 'art, sperrung'")
    ]


def test_import_wabstic_vote_invalid_values(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')
    entities = principal.entities.get(vote.date.year, {})

    errors = import_vote_wabstic(
        vote, entities, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Art',
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'Ausmittlungsstand'
                )),
                ','.join((
                    'Eidg',
                    '0',
                    '0',
                    '4'
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
                    'SortGemeinde',
                    'SortGemeindeSub',
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
                    '100',  # 'SortGemeinde',
                    '200',  # 'SortGemeindeSub',
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
                    'xxx',  # 'SortGemeinde',
                    '200',  # 'SortGemeindeSub',
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
    assert sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ]) == [
        ('sg_gemeinden', 2, '100 is unknown'),
        ('sg_gemeinden', 2, 'Could not read nays'),
        ('sg_gemeinden', 2, 'Could not read the elegible voters'),
        ('sg_gemeinden', 2, 'Could not read the empty votes'),
        ('sg_gemeinden', 2, 'Could not read the invalid votes'),
        ('sg_gemeinden', 2, 'Could not read yeas'),
        ('sg_gemeinden', 2, 'Invalid values'),
        ('sg_gemeinden', 3, 'Could not read nays'),
        ('sg_gemeinden', 3, 'Could not read the elegible voters'),
        ('sg_gemeinden', 3, 'Could not read the empty votes'),
        ('sg_gemeinden', 3, 'Could not read the invalid votes'),
        ('sg_gemeinden', 3, 'Could not read yeas'),
        ('sg_gemeinden', 3, 'Invalid id'),
        ('sg_gemeinden', 3, 'Invalid values'),
        ('sg_geschaefte', 2, 'Invalid values')
    ]


def test_import_wabstic_vote_expats(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')
    entities = principal.entities.get(vote.date.year, {})

    for entity_id, sub_entity_id in (
        ('9170', ''),
        ('0', ''),
        ('', '9170'),
        ('', '0'),
    ):
        errors = import_vote_wabstic(
            vote, entities, '0', '0',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Art',
                        'SortWahlkreis',
                        'SortGeschaeft',
                        'Ausmittlungsstand'
                    )),
                    ','.join((
                        'Eidg',
                        '0',
                        '0',
                        '0'
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
                        'SortGemeinde',
                        'SortGemeindeSub',
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
                        entity_id,  # 'SortGemeinde',
                        sub_entity_id,  # 'SortGemeindeSub',
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
        assert vote.proposal.results.filter_by(entity_id=0).one().empty == 1

# todo: test temporary results
