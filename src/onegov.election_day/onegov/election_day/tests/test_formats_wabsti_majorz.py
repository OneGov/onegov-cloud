import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_wabsti_majorz
from onegov.election_day.models import Principal
from pytest import mark


HEADERS = [
    'AnzMandate',
    'BFS',
    'EinheitBez',
    'StimmBer',
    'StimmAbgegeben',
    'StimmLeer',
    'StimmUngueltig',
    'StimmGueltig',
]

HEADERS_RESULT = [
    'ID',
    'Name',
    'Vorname',
]


@mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabsti_majorz.tar.gz'),
])
def test_import_wabsti_majorz(session, tar_file):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='majorz',
            date=date(2011, 10, 23),
            number_of_mandates=1,
        )
    )
    session.flush()
    election = session.query(Election).one()

    principal = Principal(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    # The tar file contains results from SG from the 23.10.2011
    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()
    elected = "ID,Name,Vorname\n3,Rechsteiner,Paul".encode('utf-8')

    errors = import_election_wabsti_majorz(
        election, entities,
        BytesIO(csv), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 85
    assert election.total_entities == 85
    assert election.results.count() == 85
    assert election.progress == (85, 85)
    assert round(election.turnout, 2) == 47.79
    assert election.elegible_voters == 304850
    assert election.accounted_ballots == 144529
    assert election.accounted_votes == 144529
    assert election.received_ballots == 145694
    assert election.blank_ballots == 942
    assert election.invalid_ballots == 223
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        36282, 53308, 54616
    ]
    assert election.absolute_majority == None
    assert election.allocated_mandates == 0

    errors = import_election_wabsti_majorz(
        election, entities,
        BytesIO(csv), 'text/plain',
        BytesIO(elected), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 85
    assert election.total_entities == 85
    assert election.results.count() == 85
    assert election.progress == (85, 85)
    assert round(election.turnout, 2) == 47.79
    assert election.elegible_voters == 304850
    assert election.accounted_ballots == 144529
    assert election.accounted_votes == 144529
    assert election.received_ballots == 145694
    assert election.blank_ballots == 942
    assert election.invalid_ballots == 223
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        36282, 53308, 54616
    ]
    assert election.absolute_majority == None
    assert election.allocated_mandates == 1
    assert election.elected_candidates == [('Paul', 'Rechsteiner')]


def test_import_wabsti_majorz_missing_headers(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='majorz',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Principal(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabsti_majorz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'BFS',
                    'EinheitBez',
                    'StimmBer',
                    'StimmLeer',
                    'StimmUngueltig',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Name',
                    'Vorname',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert sorted([(e.filename, e.error.interpolate()) for e in errors]) == [
        ('Elected Candidates', "Missing columns: 'id'"),
        ('Results', "Missing columns: 'stimmabgegeben'"),
    ]


def test_import_wabsti_majorz_invalid_values(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='majorz',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Principal(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabsti_majorz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'BFS',
                    'EinheitBez',
                    'StimmBer',
                    'StimmAbgegeben',
                    'StimmLeer',
                    'StimmUngueltig',
                    'KandName_1',
                    'Stimmen_1',
                    'KandName_2',
                    'Stimmen_2',
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
                    'xxx',
                    'xxx',
                )),
                ','.join((
                    '',
                    '1234',
                    '',
                    '100',
                    '90',
                    '1',
                    '1',
                    'Leere Zeilen',
                    '0',
                    'Ungültige Stimmen',
                    '0'
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'Name',
                    'Vorname',
                )),
                ','.join((
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
        ('Elected Candidates', 2, 'Unknown candidate'),
        ('Results', 2, 'Invalid election values'),
        ('Results', 2, 'Invalid entity values'),
        ('Results', 3, '1234 is unknown')
    ]


def test_import_wabsti_majorz_expats(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            type='majorz',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Principal(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    for entity_id in (9170, 0):
        errors = import_election_wabsti_majorz(
            election, entities,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'AnzMandate',
                        'BFS',
                        'EinheitBez',
                        'StimmBer',
                        'StimmAbgegeben',
                        'StimmLeer',
                        'StimmUngueltig',
                        'KandName_1',
                        'Stimmen_1',
                        'KandName_2',
                        'Stimmen_2',
                    )),
                    ','.join((
                        '',
                        str(entity_id),
                        '',
                        '100',
                        '90',
                        '1',
                        '1',
                        'Leere Zeilen',
                        '0',
                        'Ungültige Stimmen',
                        '1'
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )

        assert not errors
        assert election.results.filter_by(entity_id=0).one().invalid_votes == 1

# todo: test temporary results
