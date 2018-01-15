import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_wabstic_majorz
from onegov.election_day.models import Canton
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabstic_majorz.tar.gz'),
])
def test_import_wabstic_majorz(session, tar_file):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()

    principal = Canton(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    # The tar file contains results from SG from the 28.02.2016
    with tarfile.open(tar_file, 'r|gz') as f:
        wmstatic_gemeinden = f.extractfile(f.next()).read()
        wm_gemeinden = f.extractfile(f.next()).read()
        wm_kandidaten = f.extractfile(f.next()).read()
        wm_kandidatengde = f.extractfile(f.next()).read()
        wm_wahl = f.extractfile(f.next()).read()

    errors = import_election_wabstic_majorz(
        election, entities, '9', '9',
        BytesIO(wm_wahl), 'text/plain',
        BytesIO(wmstatic_gemeinden), 'text/plain',
        BytesIO(wm_gemeinden), 'text/plain',
        BytesIO(wm_kandidaten), 'text/plain',
        BytesIO(wm_kandidatengde), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 78
    assert election.total_entities == 78
    assert election.results.count() == 78
    assert election.absolute_majority == 79412
    assert election.elegible_voters == 311828
    assert election.accounted_ballots == 158822
    assert election.accounted_votes == 626581

    assert election.allocated_mandates == 6
    assert sorted(election.elected_candidates) == [
        ('Beni', 'Würth'),
        ('Bruno', 'Damann'),
        ('Fredy', 'Fässler'),
        ('Heidi', 'Hanselmann'),
        ('Martin', 'Klöti'),
        ('Stefan', 'Kölliker')
    ]


def test_import_wabstic_majorz_missing_headers(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabstic_majorz(
        election, entities, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'StimmenLeer',
                    'StimmenUngueltig',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'Nachname',
                    'Gewahlt',
                    'Partei',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'KNR',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        ('wm_wahl', "Missing columns: 'absolutesmehr'"),
        ('wmstatic_gemeinden', "Missing columns: 'sortgemeinde'"),
        ('wm_gemeinden', "Missing columns: 'sperrung'"),
        ('wm_kandidaten', "Missing columns: 'knr, vorname'"),
        ('wm_kandidatengde', "Missing columns: 'stimmen'")
    ]


def test_import_wabstic_majorz_invalid_values(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabstic_majorz(
        election, entities, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'AbsolutesMehr',
                    'Ausmittlungsstand',
                )),
                ','.join((
                    '0',
                    'xxx',  # AbsolutesMehr
                    '4',  # Ausmittlungsstand
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                )),
                ','.join((
                    '0',
                    '0',
                    '100',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    'xxx',  # Stimmberechtigte
                )),
                ','.join((
                    '0',
                    '0',
                    '3215',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    '10',  # Stimmberechtigte
                )),
                ','.join((
                    '0',
                    '0',
                    '3215',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    '10',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'StimmenLeer',
                    'StimmenUngueltig',
                )),
                ','.join((
                    '100',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    'xxx',  # Stimmberechtigte
                    'xxx',  # Sperrung
                    'xxx',  # StmAbgegeben
                    'xxx',  # StmLeer
                    'xxx',  # StmUngueltig
                    'xxx',  # StimmenLeer
                    'xxx',  # StimmenUngueltig
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Nachname',
                    'Vorname',
                    'Gewahlt',
                    'Partei',
                )),
                ','.join((
                    '0',
                    'xxx',  # KNR
                    'xxx',  # Nachname
                    'xxx',  # Vorname
                    'xxx',  # Gewahlt
                    'xxx',  # Partei
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '0',
                    '100',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    'yyy',  # KNR
                    'xxx',  # Stimmen
                )),
                ','.join((
                    '0',
                    '3256',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    '100',  # KNR
                    '200',  # Stimmen
                )),

            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ]) == [
        ('wm_gemeinden', 2, '100 is unknown'),
        ('wm_gemeinden', 2, 'Invalid entity values'),
        ('wm_gemeinden', 2, 'Invalid entity values'),
        ('wm_gemeinden', 2, 'Invalid entity values'),
        ('wm_kandidatengde', 2, 'Invalid candidate results'),
        ('wm_kandidatengde', 3, 'Invalid candidate results'),
        ('wm_wahl', 2, 'Invalid values'),
        ('wmstatic_gemeinden', 2, '100 is unknown'),
        ('wmstatic_gemeinden', 2, 'Could not read the elegible voters'),
        ('wmstatic_gemeinden', 4, '3215 was found twice')
    ]


def test_import_wabstic_majorz_expats(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')
    entities = principal.entities.get(election.date.year, {})

    for entity_id, sub_entity_id in (
        ('9170', ''),
        ('0', ''),
        ('', '9170'),
        ('', '0'),
    ):
        errors = import_election_wabstic_majorz(
            election, entities, '0', '0',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'AbsolutesMehr',
                        'Ausmittlungsstand',
                    )),
                    ','.join((
                        '0',
                        '5000',  # AbsolutesMehr
                        '0',  # Ausmittlungsstand
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortWahlkreis',
                        'SortGeschaeft',
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'Stimmberechtigte',
                    )),
                    ','.join((
                        '0',
                        '0',
                        entity_id,  # SortGemeinde
                        sub_entity_id,  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'StimmenLeer',
                        'StimmenUngueltig',
                    )),
                    ','.join((
                        entity_id,  # SortGemeinde
                        sub_entity_id,  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                        '',  # Sperrung
                        '',  # StmAbgegeben
                        '',  # StmLeer
                        '1',  # StmUngueltig
                        '',  # StimmenLeer
                        '1',  # StimmenUngueltig
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Nachname',
                        'Vorname',
                        'Gewahlt',
                        'Partei',
                    )),
                    ','.join((
                        '0',
                        '1',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                        '',  # Gewahlt
                        '',  # Partei
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        '0',
                        entity_id,  # SortGemeinde
                        sub_entity_id,  # SortGemeindeSub
                        '1',  # KNR
                        '10',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )

        assert not errors
        assert election.results.filter_by(entity_id=0).one().invalid_votes == 1

# todo: test temporary results
