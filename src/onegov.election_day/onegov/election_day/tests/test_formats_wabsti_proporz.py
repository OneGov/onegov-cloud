import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_wabsti_proporz
from onegov.election_day.models import Principal
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabsti_proporz.tar.gz'),
])
def test_import_wabsti_proporz(session, tar_file):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='proporz',
            date=date(2015, 10, 18),
            number_of_mandates=3,
        )
    )
    session.flush()
    election = session.query(Election).one()

    principal = Principal(canton='zg')
    entities = principal.entities.get(election.date.year, {})

    # The tar file contains results from ZG from the 18.10.2015
    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()
        connections = f.extractfile(f.next()).read()
        stats = f.extractfile(f.next()).read()

    elected = (
        'ID,Name,Vorname\n'
        '401,Pfister,Gerhard\n'
        '601,Pezzatti,Bruno\n'
        '1501,Aeschi,Thomas\n'
    ).encode('utf-8')

    errors = import_election_wabsti_proporz(
        election, entities,
        BytesIO(csv), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 11
    assert election.total_entities == 11
    assert election.results.count() == 11
    assert election.progress == (11, 11)
    assert round(election.turnout, 2) == 0
    assert election.elegible_voters == 0
    assert election.accounted_ballots == 0
    assert election.accounted_votes == 0
    assert election.received_ballots == 0
    assert election.blank_ballots == 0
    assert election.invalid_ballots == 0
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        82, 117, 132, 144, 168, 218, 222, 235, 269, 345, 394, 488, 490, 545,
        550, 555, 559, 561, 607, 629, 637, 684, 929, 1043, 1142, 1159, 1163,
        1206, 1256, 1327, 1378, 1394, 1706, 1823, 1874, 2190, 2303, 2607,
        2987, 3240, 3606, 3637, 3859, 3908, 4093, 5629, 7206, 10174, 16134,
        17034
    ]
    assert election.absolute_majority == None
    assert election.allocated_mandates == 0

    errors = import_election_wabsti_proporz(
        election, entities,
        BytesIO(csv), 'text/plain',
        BytesIO(connections), 'text/plain',
        BytesIO(elected), 'text/plain',
        BytesIO(stats), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 11
    assert election.total_entities == 11
    assert election.results.count() == 11
    assert election.progress == (11, 11)
    assert round(election.turnout, 2) == 53.74
    assert election.elegible_voters == 74803
    assert election.accounted_ballots == 39067
    assert election.accounted_votes == 116689
    assert election.received_ballots == 40200
    assert election.blank_ballots == 118
    assert election.invalid_ballots == 1015
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        82, 117, 132, 144, 168, 218, 222, 235, 269, 345, 394, 488, 490, 545,
        550, 555, 559, 561, 607, 629, 637, 684, 929, 1043, 1142, 1159, 1163,
        1206, 1256, 1327, 1378, 1394, 1706, 1823, 1874, 2190, 2303, 2607,
        2987, 3240, 3606, 3637, 3859, 3908, 4093, 5629, 7206, 10174, 16134,
        17034
    ]
    assert election.absolute_majority == None
    assert election.allocated_mandates == 3
    assert sorted(election.elected_candidates) == [
        ('Bruno', 'Pezzatti'), ('Gerhard', 'Pfister'), ('Thomas', 'Aeschi')
    ]
    assert sorted((l.votes for l in election.lists)) == [
        347, 575, 807, 1128, 1333, 1701, 2186, 3314, 4178, 4299, 4436, 5844,
        6521, 8868, 16285, 24335, 30532
    ]
    assert sorted((c.votes for c in election.list_connections)) == [
        0, 1128, 4178, 8352, 16048, 20584, 30856, 35543
    ]


def test_import_wabsti_proporz_missing_headers(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='proporz',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Principal(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabsti_proporz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Liste_KandID',
                    'Kand_Nachname',
                    'Kand_Vorname',
                    'Liste_ID',
                    'Liste_Code',
                    'Kand_StimmenTotal',
                    'Liste_ParteistimmenTotal',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Liste',
                    'LUV',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ignore1',
                    'ignore2',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Einheit_Name',
                    'StimBerTotal',
                    'WZEingegangen',
                    'WZUngueltig',
                    'StmWZVeraendertLeerAmtlLeer',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert sorted([(e.filename, e.error.interpolate()) for e in errors]) == [
        ('Elected Candidates', "Missing columns: 'id'"),
        ('Election statistics', "Missing columns: 'wzleer'"),
        ('List connections', "Missing columns: 'lv'"),
        ('Results', "Missing columns: 'einheit_name'")
    ]


def test_import_wabsti_proporz_invalid_values(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='proporz',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Principal(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabsti_proporz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Einheit_Name',
                    'Liste_KandID',
                    'Kand_Nachname',
                    'Kand_Vorname',
                    'Liste_ID',
                    'Liste_Code',
                    'Kand_StimmenTotal',
                    'Liste_ParteistimmenTotal',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                )),
                ','.join((
                    '1234',
                    'xxx',
                    '7',
                    'xxx',
                    'xxx',
                    '8',
                    '9',
                    '50',
                    '60',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Liste',
                    'LV',
                    'LUV',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'ignore1',
                    'ignore2',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                )),
                ','.join((
                    '1',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Einheit_Name',
                    'StimBerTotal',
                    'WZEingegangen',
                    'WZLeer',
                    'WZUngueltig',
                    'StmWZVeraendertLeerAmtlLeer',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )

    assert sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ]) == [
        ('Elected Candidates', 2, 'Invalid values'),
        ('Elected Candidates', 3, 'Unknown candidate'),
        ('Election statistics', 2, 'Invalid values'),
        ('List connections', 2, 'Invalid list connection values'),
        ('Results', 2, 'Invalid candidate results'),
        ('Results', 2, 'Invalid candidate values'),
        ('Results', 2, 'Invalid entity values'),
        ('Results', 2, 'Invalid list results'),
        ('Results', 2, 'Invalid list results'),
        ('Results', 2, 'Invalid list values'),
        ('Results', 3, '1234 is unknown')
    ]


def test_import_wabsti_proporz_expats(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='proporz',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Principal(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    for entity_id in (9170, 0):
        errors = import_election_wabsti_proporz(
            election, entities,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Einheit_BFS',
                        'Einheit_Name',
                        'Liste_KandID',
                        'Kand_Nachname',
                        'Kand_Vorname',
                        'Liste_ID',
                        'Liste_Code',
                        'Kand_StimmenTotal',
                        'Liste_ParteistimmenTotal',
                    )),
                    ','.join((
                        str(entity_id),
                        'xxx',
                        '7',
                        'xxx',
                        'xxx',
                        '8',
                        '9',
                        '50',
                        '60',
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
        )

        assert not errors

        candidate = election.candidates.one()
        assert candidate.results.one().election_result.entity_id == 0
        assert candidate.votes == 50

# todo: test temporary results
