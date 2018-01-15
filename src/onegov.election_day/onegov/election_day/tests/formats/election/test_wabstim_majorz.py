import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_wabstim_majorz
from onegov.election_day.models import Municipality
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabstim_majorz.tar.gz'),
])
def test_import_wabstim_majorz(session, tar_file):
    session.add(
        Election(
            title='election',
            domain='municipality',
            date=date(2016, 9, 25),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()

    principal = Municipality(municipality='3231', name='Au')
    entities = principal.entities.get(election.date.year, {})

    # The tar file contains results from AU from the 25.9.2016
    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    errors = import_election_wabstim_majorz(
        election, entities,
        BytesIO(csv), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 1
    assert election.total_entities == 1
    assert election.results.count() == 1
    assert election.progress == (1, 1)
    assert round(election.turnout, 2) == 27.03
    assert election.elegible_voters == 4021
    assert election.received_ballots == 1087
    assert election.accounted_ballots == 1036
    assert election.blank_ballots == 28
    assert election.invalid_ballots == 23
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        556, 665, 678, 715, 790, 810, 830
    ]
    assert election.absolute_majority == 519
    assert election.allocated_mandates == 6
    assert sorted(election.elected_candidates) == [
        ('Alex', 'Frei'),
        ('Carola', 'Espanhol'),
        ('Ernst', 'Brändle'),
        ('Franco', 'Frisenda'),
        ('Gloria', 'Schöbi'),
        ('Markus', 'Bernet')
    ]


def test_import_wabstim_majorz_utf16(session):
    session.add(
        Election(
            title='election',
            domain='municipality',
            date=date(2011, 10, 23),
            number_of_mandates=1,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Municipality(municipality='3427')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabstim_majorz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'AbsolutesMehr',
                    'BFS',
                    'StimmBer',
                    'WzAbgegeben',
                    'WzLeer',
                    'WzUngueltig',
                )),
            ))
        ).encode('utf-16-le')), 'text/plain'
    )
    assert [e.error for e in errors] == ['No data found']


def test_import_wabstim_majorz_missing_headers(session):
    session.add(
        Election(
            title='election',
            domain='municipality',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Municipality(municipality='3427')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabstim_majorz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'AbsolutesMehr',
                    'BFS',
                    'StimmBer',
                    'WzAbgegeben',
                    'WzUngueltig',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert sorted([e.error.interpolate() for e in errors]) == [
        "Missing columns: 'wzleer'"
    ]


def test_import_wabstim_majorz_invalid_values(session):
    session.add(
        Election(
            title='election',
            domain='municipality',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Municipality(municipality='3427')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabstim_majorz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'AbsolutesMehr',
                    'BFS',
                    'StimmBer',
                    'WzAbgegeben',
                    'WzLeer',
                    'WzUngueltig',
                    'KandName_1',
                    'KandVorname_1',
                    'Stimmen_1',
                    'KandResultArt_1',
                    'KandName_2',
                    'KandVorname_2',
                    'Stimmen_2',
                    'KandResultArt_2',
                    'KandName_3',
                    'KandVorname_3',
                    'Stimmen_3',
                    'KandResultArt_3',
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
                    '1',
                    '1000',
                    '3427',
                    '5000',
                    '4000',
                    '100',
                    '200',
                    'Leere Zeilen',
                    '',
                    '300',
                    '9',
                    'Ungültige Stimmen',
                    '',
                    '400',
                    '9',
                    'xxxx',
                    'xxxx',
                    '0',
                    'xxxx',
                )),
                ','.join((
                    '1',
                    '1000',
                    '3427',
                    '5000',
                    '4000',
                    '100',
                    '200',
                    'Leere Zeilen',
                    '',
                    '300',
                    '9',
                    'Ungültige Stimmen',
                    '',
                    '400',
                    '9',
                    'Meier',
                    'Peter',
                    '1800',
                    '2',
                )),
                ','.join((
                    '1',
                    '1000',
                    '3428',
                    '5000',
                    '4000',
                    '100',
                    '200',
                    'Leere Zeilen',
                    '',
                    '300',
                    '9',
                    'Ungültige Stimmen',
                    '',
                    '400',
                    '9',
                    'Meier',
                    'Peter',
                    '1800',
                    '2',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert sorted([(e.line, e.error.interpolate()) for e in errors]) == [
        (2, 'Invalid election values'),
        (2, 'Invalid entity values'),
        (3, 'Invalid candidate values'),
        (4, '3427 was found twice'),
        (5, '3428 is unknown')
    ]


def test_import_wabstim_majorz_expats(session):
    session.add(
        Election(
            title='election',
            domain='municipality',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Municipality(municipality='3427')
    entities = principal.entities.get(election.date.year, {})

    for entity_id in (9170, 0):
        errors = import_election_wabstim_majorz(
            election, entities,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'AnzMandate',
                        'AbsolutesMehr',
                        'BFS',
                        'StimmBer',
                        'WzAbgegeben',
                        'WzLeer',
                        'WzUngueltig',
                        'KandName_1',
                        'KandVorname_1',
                        'Stimmen_1',
                        'KandResultArt_1',
                        'KandName_2',
                        'KandVorname_2',
                        'Stimmen_2',
                        'KandResultArt_2',
                        'KandName_3',
                        'KandVorname_3',
                        'Stimmen_3',
                        'KandResultArt_3',
                    )),
                    ','.join((
                        '1',
                        '1000',
                        '0',
                        '5000',
                        '4000',
                        '100',
                        '200',
                        'Leere Zeilen',
                        '',
                        '300',
                        '9',
                        'Ungültige Stimmen',
                        '',
                        '400',
                        '9',
                        'Meier',
                        'Peter',
                        '1800',
                        '2',
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert '0 is unknown' in [e.error.interpolate() for e in errors]

# todo: test temporary results
