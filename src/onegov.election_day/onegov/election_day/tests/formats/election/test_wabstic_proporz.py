import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.ballot import List
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_wabstic_proporz
from onegov.election_day.models import Canton
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day',
                'tests/fixtures/wabstic_proporz.tar.gz'),
])
def test_import_wabstic_proporz(session, tar_file):
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=12,
        )
    )
    session.flush()
    election = session.query(Election).one()

    principal = Canton(canton='sg')

    # The tar file contains
    #  - cantonal results from SG from the 18.10.2015
    #  - regional results from SG from the 28.02.2016
    with tarfile.open(tar_file, 'r|gz') as f:
        cantonal_wpstatic_gemeinden = f.extractfile(f.next()).read()
        cantonal_wpstatic_kandidaten = f.extractfile(f.next()).read()
        cantonal_wp_gemeinden = f.extractfile(f.next()).read()
        cantonal_wp_kandidaten = f.extractfile(f.next()).read()
        cantonal_wp_kandidatengde = f.extractfile(f.next()).read()
        cantonal_wp_listen = f.extractfile(f.next()).read()
        cantonal_wp_listengde = f.extractfile(f.next()).read()
        cantonal_wp_wahl = f.extractfile(f.next()).read()
        regional_wpstatic_gemeinden = f.extractfile(f.next()).read()
        regional_wpstatic_kandidaten = f.extractfile(f.next()).read()
        regional_wp_gemeinden = f.extractfile(f.next()).read()
        regional_wp_kandidaten = f.extractfile(f.next()).read()
        regional_wp_kandidatengde = f.extractfile(f.next()).read()
        regional_wp_listen = f.extractfile(f.next()).read()
        regional_wp_listengde = f.extractfile(f.next()).read()
        regional_wp_wahl = f.extractfile(f.next()).read()

    # Test cantonal election
    errors = import_election_wabstic_proporz(
        election, principal, '1', None,
        BytesIO(cantonal_wp_wahl), 'text/plain',
        BytesIO(cantonal_wpstatic_gemeinden), 'text/plain',
        BytesIO(cantonal_wp_gemeinden), 'text/plain',
        BytesIO(cantonal_wp_listen), 'text/plain',
        BytesIO(cantonal_wp_listengde), 'text/plain',
        BytesIO(cantonal_wpstatic_kandidaten), 'text/plain',
        BytesIO(cantonal_wp_kandidaten), 'text/plain',
        BytesIO(cantonal_wp_kandidatengde), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.progress == (78, 78)
    assert election.absolute_majority is None
    assert election.eligible_voters == 317969
    assert election.accounted_ballots == 145631
    assert election.accounted_votes == 1732456

    assert election.allocated_mandates == 12
    assert sorted(election.elected_candidates) == [
        ('Barbara', 'Gysi'),
        ('Barbara', 'Keller-Inhelder'),
        ('Claudia', 'Friedl'),
        ('Jakob', 'Büchler'),
        ('Lukas', 'Reimann'),
        ('Marcel', 'Dobler'),
        ('Markus', 'Ritter'),
        ('Roland Rino', 'Büchel'),
        ('Thomas', 'Ammann'),
        ('Thomas', 'Müller'),
        ('Toni', 'Brunner'),
        ('Walter', 'Müller')
    ]

    assert sorted([
        (l.name, l.number_of_mandates)
        for l in election.lists.filter(List.number_of_mandates > 0)
    ]) == [('CVP', 3), ('FDP', 2), ('SP', 2), ('SVP', 5)]
    assert election.lists.filter(List.name == 'SVP').one().votes == 620183

    assert sorted((c.votes for c in election.list_connections))[-1] == 636317

    # Test regional elections
    election.domain = 'region'
    election.date = date(2016, 2, 28)

    for number, district, mandates, entities, votes, turnout in (
        ('1', '1', 29, 9, 949454, 44.45),  # SG
        ('2', '2', 10, 9, 105959, 43.07),  # RO
        ('3', '3', 17, 13, 318662, 46.86),  # RH
        ('4', '5', 9, 6, 83098, 43.94),  # WE
        ('5', '6', 10, 8, 119157, 48.10),  # SA
        ('6', '7', 16, 10, 301843, 44.65),  # SE
        ('7', '8', 11, 12, 159038, 49.15),  # TO
        ('8', '13', 18, 10, 352595, 43.94),  # WI
    ):
        election.number_of_mandates = mandates

        errors = import_election_wabstic_proporz(
            election, principal, number, district,
            BytesIO(regional_wp_wahl), 'text/plain',
            BytesIO(regional_wpstatic_gemeinden), 'text/plain',
            BytesIO(regional_wp_gemeinden), 'text/plain',
            BytesIO(regional_wp_listen), 'text/plain',
            BytesIO(regional_wp_listengde), 'text/plain',
            BytesIO(regional_wpstatic_kandidaten), 'text/plain',
            BytesIO(regional_wp_kandidaten), 'text/plain',
            BytesIO(regional_wp_kandidatengde), 'text/plain',
        )

        assert not errors
        assert election.completed
        assert election.progress == (entities, entities)
        assert election.accounted_votes == votes
        assert round(election.turnout, 2) == turnout


def test_import_wabstic_proporz_missing_headers(session):
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabstic_proporz(
        election, principal, '0', '0',
        BytesIO('Ausmittlungsstand,\n'.encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortWahlkreis',
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'AnzWZAmtLeer',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ListNr',
                    'ListCode',
                    'Sitze',
                    'ListVerb',
                    'ListUntVerb',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGemeindeSub',
                    'ListNr',
                    'StimmenTotal',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'KNR',
                    'Nachname',
                    'Vorname',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'KNR',
                    'Gewahlt',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGemeindeSub',
                    'KNR',
                    'Stimmen',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert sorted([(e.filename, e.error.interpolate()) for e in errors]) == [
        ('wp_gemeinden', "Missing columns: 'sortgemeinde'"),
        ('wp_kandidaten', "Missing columns: 'sortgeschaeft'"),
        ('wp_kandidatengde', "Missing columns: 'sortgemeinde'"),
        ('wp_listen', "Missing columns: 'sortgeschaeft'"),
        ('wp_listengde', "Missing columns: 'sortgemeinde'"),
        ('wp_wahl', "Missing columns: 'sortgeschaeft'"),
        ('wpstatic_gemeinden', "Missing columns: 'sortgeschaeft'"),
        ('wpstatic_kandidaten', "Missing columns: 'sortgeschaeft'"),
    ]


def test_import_wabstic_proporz_invalid_values(session):
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabstic_proporz(
        election, principal, '0', '0',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                )),
                ','.join((
                    '0',
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
                    '',  # Stimmberechtigte
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
                    'AnzWZAmtLeer',
                )),
                ','.join((
                    '3215',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    'xxx',  # Stimmberechtigte
                    'xxx',  # Sperrung
                    'xxx',  # StmAbgegeben
                    'xxx',  # StmLeer
                    'xxx',  # StmUngueltig
                    'xxx',  # AnzWZAmtLeer
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'ListNr',
                    'ListCode',
                    'Sitze',
                    'ListVerb',
                    'ListUntVerb',
                )),
                ','.join((
                    '0',
                    'xxx',  # ListNr
                    'xxx',  # ListCode
                    'xxx',  # Sitze
                    'xxx',  # ListVerb
                    'xxx',  # ListUntVerb
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'ListNr',
                    'StimmenTotal',
                )),
                ','.join((
                    '100',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    'xxx',  # ListNr
                    'xxx',  # StimmenTotal
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
                )),
                ','.join((
                    '0',
                    'xxx',  # KNR
                    'xxx',  # Nachname
                    'xxx',  # Vorname
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Gewahlt',
                )),
                ','.join((
                    '0',
                    'xxx',  # KNR
                    'xxx',  # Gewahlt
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '100',  # SortGemeinde
                    '200',  # SortGemeindeSub
                    'xxx',  # KNR
                    'xxx',  # Stimmen
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ]) == [
        ('wp_gemeinden', 2, 'Invalid entity values'),
        ('wp_gemeinden', 2, 'Invalid entity values'),
        ('wp_gemeinden', 2, 'Invalid entity values'),
        ('wp_kandidatengde', 2, 'Invalid candidate results'),
        ('wp_listen', 2, 'Invalid list values'),
        ('wp_listengde', 2, 'Invalid list results'),
        ('wp_wahl', 2, 'Invalid values'),
        ('wpstatic_gemeinden', 2, '100 is unknown'),
        ('wpstatic_kandidaten', 2, 'Invalid candidate values'),
        ('wpstatic_kandidaten', 2, 'Invalid candidate values')
    ]


def test_import_wabstic_proporz_expats(session):
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    for entity_id, sub_entity_id in (
        ('9170', ''),
        ('0', ''),
        ('', '9170'),
        ('', '0'),
    ):
        errors = import_election_wabstic_proporz(
            election, principal, '0', '0',
            BytesIO((  # wp_wahl
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'Ausmittlungsstand',
                    )),
                    ','.join((
                        '0',
                        '0',  # Ausmittlungsstand
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_gemeinden
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
                        '',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_gemeinden
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'AnzWZAmtLeer',
                    )),
                    ','.join((
                        entity_id,  # SortGemeinde
                        sub_entity_id,  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                        '',  # Sperrung
                        '',  # StmAbgegeben
                        '1',  # StmLeer
                        '',  # StmUngueltig
                        '',  # AnzWZAmtLeer
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listen
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'ListNr',
                        'ListCode',
                        'Sitze',
                        'ListVerb',
                        'ListUntVerb',
                    )),
                    ','.join((
                        '0',
                        '1',  # ListNr
                        '1',  # ListCode
                        '',  # Sitze
                        '',  # ListVerb
                        '',  # ListUntVerb
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'ListNr',
                        'StimmenTotal',
                    )),
                    ','.join((
                        entity_id,  # SortGemeinde
                        sub_entity_id,  # SortGemeindeSub
                        '1',  # ListNr
                        '0',  # StimmenTotal
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Nachname',
                        'Vorname',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Gewahlt',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        '',  # Gewahlt
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidatengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        entity_id,  # SortGemeinde
                        sub_entity_id,  # SortGemeindeSub
                        '101',  # KNR
                        '100',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )

        assert not errors
        assert election.results.filter_by(entity_id=0).one().blank_ballots == 1


def test_import_wabstic_proporz_temporary_results(session):
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabstic_proporz(
        election, principal, '0', '0',
        BytesIO((  # wp_wahl
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                )),
                ','.join((
                    '0',
                    '0',  # Ausmittlungsstand
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wpstatic_gemeinden
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
                    '3203',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '',  # Stimmberechtigte
                )),
                ','.join((
                    '0',
                    '0',
                    '3204',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_gemeinden
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'AnzWZAmtLeer',
                )),
                ','.join((
                    '3203',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '10000',  # Stimmberechtigte
                    '1200',  # Sperrung
                    '',  # StmAbgegeben
                    '1',  # StmLeer
                    '',  # StmUngueltig
                    '',  # AnzWZAmtLeer
                )),
                ','.join((
                    '3204',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '10000',  # Stimmberechtigte
                    '',  # Sperrung
                    '',  # StmAbgegeben
                    '1',  # StmLeer
                    '',  # StmUngueltig
                    '',  # AnzWZAmtLeer
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_listen
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'ListNr',
                    'ListCode',
                    'Sitze',
                    'ListVerb',
                    'ListUntVerb',
                )),
                ','.join((
                    '0',
                    '1',  # ListNr
                    '1',  # ListCode
                    '',  # Sitze
                    '',  # ListVerb
                    '',  # ListUntVerb
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_listengde
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'ListNr',
                    'StimmenTotal',
                )),
                ','.join((
                    '3203',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '1',  # ListNr
                    '0',  # StimmenTotal
                )),
                ','.join((
                    '3204',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '1',  # ListNr
                    '0',  # StimmenTotal
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wpstatic_kandidaten
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Nachname',
                    'Vorname',
                )),
                ','.join((
                    '0',
                    '101',  # KNR
                    'xxx',  # Nachname
                    'xxx',  # Vorname
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_kandidaten
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Gewahlt',
                )),
                ','.join((
                    '0',
                    '101',  # KNR
                    '',  # Gewahlt
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_kandidatengde
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '3203',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '101',  # KNR
                    '100',  # Stimmen
                )),
                ','.join((
                    '3204',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '101',  # KNR
                    '100',  # Stimmen
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert not errors

    # 1 Counted, 1 Uncounted, 75 Missing
    assert election.progress == (1, 77)


def test_import_wabstic_proporz_regional(session):
    session.add(
        ProporzElection(
            title='election',
            domain='region',
            date=date(2018, 2, 19),
            number_of_mandates=1
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal_zg = Canton(canton='zg')
    principal_sg = Canton(canton='sg')

    # Too many districts
    for distinct in (False, True):
        election.distinct = distinct
        expected = ['No clear district'] if distinct else []

        errors = import_election_wabstic_proporz(
            election, principal_zg, '0', '0',
            BytesIO((  # wp_wahl
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'Ausmittlungsstand',
                    )),
                    ','.join((
                        '0',
                        '0',  # Ausmittlungsstand
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_gemeinden
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
                        '1701',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '',  # Stimmberechtigte
                    )),
                    ','.join((
                        '0',
                        '0',
                        '1702',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_gemeinden
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'AnzWZAmtLeer',
                    )),
                    ','.join((
                        '1701',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                        '1200',  # Sperrung
                        '',  # StmAbgegeben
                        '1',  # StmLeer
                        '',  # StmUngueltig
                        '',  # AnzWZAmtLeer
                    )),
                    ','.join((
                        '1702',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                        '',  # Sperrung
                        '',  # StmAbgegeben
                        '1',  # StmLeer
                        '',  # StmUngueltig
                        '',  # AnzWZAmtLeer
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listen
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'ListNr',
                        'ListCode',
                        'Sitze',
                        'ListVerb',
                        'ListUntVerb',
                    )),
                    ','.join((
                        '0',
                        '1',  # ListNr
                        '1',  # ListCode
                        '',  # Sitze
                        '',  # ListVerb
                        '',  # ListUntVerb
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'ListNr',
                        'StimmenTotal',
                    )),
                    ','.join((
                        '1701',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '1',  # ListNr
                        '0',  # StimmenTotal
                    )),
                    ','.join((
                        '1702',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '1',  # ListNr
                        '0',  # StimmenTotal
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Nachname',
                        'Vorname',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Gewahlt',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        '',  # Gewahlt
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidatengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        '1701',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '101',  # KNR
                        '100',  # Stimmen
                    )),
                    ','.join((
                        '1702',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '101',  # KNR
                        '100',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert [error.error for error in errors] == expected

        errors = import_election_wabstic_proporz(
            election, principal_sg, '0', '0',
            BytesIO((  # wp_wahl
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'Ausmittlungsstand',
                    )),
                    ','.join((
                        '0',
                        '0',  # Ausmittlungsstand
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_gemeinden
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
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '',  # Stimmberechtigte
                    )),
                    ','.join((
                        '0',
                        '0',
                        '3276',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_gemeinden
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'AnzWZAmtLeer',
                    )),
                    ','.join((
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                        '1200',  # Sperrung
                        '',  # StmAbgegeben
                        '1',  # StmLeer
                        '',  # StmUngueltig
                        '',  # AnzWZAmtLeer
                    )),
                    ','.join((
                        '3276',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                        '',  # Sperrung
                        '',  # StmAbgegeben
                        '1',  # StmLeer
                        '',  # StmUngueltig
                        '',  # AnzWZAmtLeer
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listen
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'ListNr',
                        'ListCode',
                        'Sitze',
                        'ListVerb',
                        'ListUntVerb',
                    )),
                    ','.join((
                        '0',
                        '1',  # ListNr
                        '1',  # ListCode
                        '',  # Sitze
                        '',  # ListVerb
                        '',  # ListUntVerb
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'ListNr',
                        'StimmenTotal',
                    )),
                    ','.join((
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '1',  # ListNr
                        '0',  # StimmenTotal
                    )),
                    ','.join((
                        '3276',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '1',  # ListNr
                        '0',  # StimmenTotal
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Nachname',
                        'Vorname',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Gewahlt',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        '',  # Gewahlt
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidatengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '101',  # KNR
                        '100',  # Stimmen
                    )),
                    ','.join((
                        '3276',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '101',  # KNR
                        '100',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert [error.error for error in errors] == expected

    # OK
    election.distinct = True
    errors = import_election_wabstic_proporz(
        election, principal_zg, '0', '0',
        BytesIO((  # wp_wahl
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                )),
                ','.join((
                    '0',
                    '0',  # Ausmittlungsstand
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wpstatic_gemeinden
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
                    '1701',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_gemeinden
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'AnzWZAmtLeer',
                )),
                ','.join((
                    '1701',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '10000',  # Stimmberechtigte
                    '1200',  # Sperrung
                    '',  # StmAbgegeben
                    '1',  # StmLeer
                    '',  # StmUngueltig
                    '',  # AnzWZAmtLeer
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_listen
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'ListNr',
                    'ListCode',
                    'Sitze',
                    'ListVerb',
                    'ListUntVerb',
                )),
                ','.join((
                    '0',
                    '1',  # ListNr
                    '1',  # ListCode
                    '',  # Sitze
                    '',  # ListVerb
                    '',  # ListUntVerb
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_listengde
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'ListNr',
                    'StimmenTotal',
                )),
                ','.join((
                    '1701',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '1',  # ListNr
                    '0',  # StimmenTotal
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wpstatic_kandidaten
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Nachname',
                    'Vorname',
                )),
                ','.join((
                    '0',
                    '101',  # KNR
                    'xxx',  # Nachname
                    'xxx',  # Vorname
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_kandidaten
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Gewahlt',
                )),
                ','.join((
                    '0',
                    '101',  # KNR
                    '',  # Gewahlt
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_kandidatengde
            '\n'.join((
                ','.join((
                    'SortGemeinde',
                    'SortGemeindeSub',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '1701',  # SortGemeinde
                    '',  # SortGemeindeSub
                    '101',  # KNR
                    '100',  # Stimmen
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert not errors
    assert election.progress == (1, 1)

    # Temporary
    for distinct, total in ((False, 1), (True, 13)):
        election.distinct = distinct

        errors = import_election_wabstic_proporz(
            election, principal_sg, '0', '0',
            BytesIO((  # wp_wahl
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'Ausmittlungsstand',
                    )),
                    ','.join((
                        '0',
                        '0',  # Ausmittlungsstand
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_gemeinden
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
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_gemeinden
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'AnzWZAmtLeer',
                    )),
                    ','.join((
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '10000',  # Stimmberechtigte
                        '1200',  # Sperrung
                        '',  # StmAbgegeben
                        '1',  # StmLeer
                        '',  # StmUngueltig
                        '',  # AnzWZAmtLeer
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listen
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'ListNr',
                        'ListCode',
                        'Sitze',
                        'ListVerb',
                        'ListUntVerb',
                    )),
                    ','.join((
                        '0',
                        '1',  # ListNr
                        '1',  # ListCode
                        '',  # Sitze
                        '',  # ListVerb
                        '',  # ListUntVerb
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_listengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'ListNr',
                        'StimmenTotal',
                    )),
                    ','.join((
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '1',  # ListNr
                        '0',  # StimmenTotal
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wpstatic_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Nachname',
                        'Vorname',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidaten
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'KNR',
                        'Gewahlt',
                    )),
                    ','.join((
                        '0',
                        '101',  # KNR
                        '',  # Gewahlt
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((  # wp_kandidatengde
                '\n'.join((
                    ','.join((
                        'SortGemeinde',
                        'SortGemeindeSub',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        '3231',  # SortGemeinde
                        '',  # SortGemeindeSub
                        '101',  # KNR
                        '100',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert not errors
        assert election.progress == (1, total)
