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
    entities = principal.entities.get(election.date.year, {})

    # The tar file contains results from SG from the 18.10.2015
    with tarfile.open(tar_file, 'r|gz') as f:
        wpstatic_gemeinden = f.extractfile(f.next()).read()
        wpstatic_kandidaten = f.extractfile(f.next()).read()
        wp_gemeinden = f.extractfile(f.next()).read()
        wp_kandidaten = f.extractfile(f.next()).read()
        wp_kandidatengde = f.extractfile(f.next()).read()
        wp_listen = f.extractfile(f.next()).read()
        wp_listengde = f.extractfile(f.next()).read()
        wp_wahl = f.extractfile(f.next()).read()

    errors = import_election_wabstic_proporz(
        election, entities, '1', '1',
        BytesIO(wp_wahl), 'text/plain',
        BytesIO(wpstatic_gemeinden), 'text/plain',
        BytesIO(wp_gemeinden), 'text/plain',
        BytesIO(wp_listen), 'text/plain',
        BytesIO(wp_listengde), 'text/plain',
        BytesIO(wpstatic_kandidaten), 'text/plain',
        BytesIO(wp_kandidaten), 'text/plain',
        BytesIO(wp_kandidatengde), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 78
    assert election.total_entities == 78
    assert election.results.count() == 78
    assert election.absolute_majority is None
    assert election.elegible_voters == 317969
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
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabstic_proporz(
        election, entities, '0', '0',
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
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        ('wp_wahl', "Missing columns: 'sortgeschaeft'"),
        ('wpstatic_gemeinden', "Missing columns: 'sortgeschaeft'"),
        ('wp_gemeinden', "Missing columns: 'sortgemeinde'"),
        ('wp_listen', "Missing columns: 'sortgeschaeft'"),
        ('wp_listengde', "Missing columns: 'sortgemeinde'"),
        ('wpstatic_kandidaten', "Missing columns: 'sortgeschaeft'"),
        ('wp_kandidaten', "Missing columns: 'sortgeschaeft'"),
        ('wp_kandidatengde', "Missing columns: 'sortgemeinde'")
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
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_wabstic_proporz(
        election, entities, '0', '0',
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
                    '100',  # SortGemeinde
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
        ('wp_gemeinden', 2, '100 is unknown'),
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
    entities = principal.entities.get(election.date.year, {})

    for entity_id, sub_entity_id in (
        ('9170', ''),
        ('0', ''),
        ('', '9170'),
        ('', '0'),
    ):
        errors = import_election_wabstic_proporz(
            election, entities, '0', '0',
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

# todo: test temporary results
