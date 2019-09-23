from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.election_day.formats import import_election_wabstic_majorz
from onegov.election_day.models import Canton

from tests.onegov.election_day.common import print_errors


def test_import_wabstic_majorz_1(session, import_test_datasets):

    election, errors = import_test_datasets(
        'wabstic',
        'election',
        'sg',
        'canton',
        election_type='majorz',
        number_of_mandates=6,
        date_=date(2016, 2, 28),
        dataset_name='regierungsratswahlen-2016',
        expats=True,
        election_number='9',
        election_district='1'
    )

    assert not errors
    assert election.completed
    assert election.progress == (78, 78)
    assert election.results.count() == 78
    assert election.absolute_majority == 79412
    assert election.eligible_voters == 311828
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

    errors = import_election_wabstic_majorz(
        election, principal, '0', '0',
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
                    'Stimmberechtigte',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
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
                    'Gewaehlt',
                    'Partei',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'KNR',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        ('wm_wahl', "Missing columns: 'absolutesmehr'"),
        ('wmstatic_gemeinden', "Missing columns: 'bfsnrgemeinde'"),
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

    errors = import_election_wabstic_majorz(
        election, principal, '0', '0',
        BytesIO((       # wm_wahl
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
        BytesIO((       # wmstatic_gemeinden
            '\n'.join((
                ','.join((
                    'SortWahlkreis',
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                )),
                ','.join((
                    '0',
                    '0',
                    '100',  # BfsNrGemeinde
                    'xxx',  # Stimmberechtigte
                )),
                ','.join((
                    '0',
                    '0',
                    '3215',  # BfsNrGemeinde
                    '10',  # Stimmberechtigte
                )),
                ','.join((
                    '0',
                    '0',
                    '3215',  # BfsNrGemeinde
                    '10',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((       # wm_gemeinden
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'StimmenLeer',
                    'StimmenUngueltig',
                )),
                ','.join((
                    '3215',  # BfsNrGemeinde
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
        BytesIO((       # wm_kandidaten
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Nachname',
                    'Vorname',
                    'Gewaehlt',
                    'Partei',
                )),
                ','.join((
                    '0',
                    'xxx',  # KNR
                    'xxx',  # Nachname
                    'xxx',  # Vorname
                    'xxx',  # Gewaehlt
                    'xxx',  # Partei
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((       # wm_kandidatengde
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '0',
                    '100',  # BfsNrGemeinde
                    'yyy',  # KNR
                    'xxx',  # Stimmen
                )),
                ','.join((
                    '0',
                    '3256',  # BfsNrGemeinde
                    '100',  # KNR
                    '200',  # Stimmen
                )),

            ))
        ).encode('utf-8')), 'text/plain'
    )
    print_errors(errors)
    assert sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ]) == [
        ('wm_gemeinden', 2, 'Invalid integer: sperrung'),
        ('wm_gemeinden', 2, 'Invalid integer: stimmberechtigte'),
        ('wm_gemeinden', 2, 'Invalid integer: stmabgegeben'),
        ('wm_kandidatengde', 2, 'Invalid candidate results'),
        ('wm_kandidatengde', 3, 'Candidate with id 100 not in wm_kandidaten'),
        ('wm_kandidatengde', 3,
            'Entity with id 3256 not in wmstatic_gemeinden'),
        ('wm_wahl', 2, 'Invalid integer: absolutesmehr'),
        ('wm_wahl', 2, 'Value of ausmittlungsstand not between 0 and 3'),
        ('wmstatic_gemeinden', 2, '100 is unknown'),
        ('wmstatic_gemeinden', 2, 'Invalid integer: stimmberechtigte'),
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

    for expats in (False, True):
        election.expats = expats
        for entity_id in ('9170', '0'):
            errors = import_election_wabstic_majorz(
                election, principal, '0', '0',
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
                            'BfsNrGemeinde',
                            'Stimmberechtigte',
                        )),
                        ','.join((
                            '0',
                            '0',
                            entity_id,  # BfsNrGemeinde
                            '10000',  # Stimmberechtigte
                        )),
                    ))
                ).encode('utf-8')), 'text/plain',
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'BfsNrGemeinde',
                            'Stimmberechtigte',
                            'Sperrung',
                            'StmAbgegeben',
                            'StmLeer',
                            'StmUngueltig',
                            'StimmenLeer',
                            'StimmenUngueltig',
                        )),
                        ','.join((
                            entity_id,  # BfsNrGemeinde
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
                            'Gewaehlt',
                            'Partei',
                        )),
                        ','.join((
                            '0',
                            '1',  # KNR
                            'xxx',  # Nachname
                            'xxx',  # Vorname
                            '',  # Gewaehlt
                            '',  # Partei
                        )),
                    ))
                ).encode('utf-8')), 'text/plain',
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'SortGeschaeft',
                            'BfsNrGemeinde',
                            'KNR',
                            'Stimmen',
                        )),
                        ','.join((
                            '0',
                            entity_id,  # BfsNrGemeinde
                            '1',  # KNR
                            '10',  # Stimmen
                        )),
                    ))
                ).encode('utf-8')), 'text/plain'
            )
            errors = [(e.line, e.error.interpolate()) for e in errors]
            result = election.results.filter_by(entity_id=0).first()
            if expats:
                assert errors == []
                assert result.invalid_votes == 1
            else:
                assert errors == []
                assert result is None


def test_import_wabstic_majorz_temporary_results(session):
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

    errors = import_election_wabstic_majorz(
        election, principal, '0', '0',
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
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                )),
                ','.join((
                    '0',
                    '0',
                    '3203',  # BfsNrGemeinde
                    '10000',  # Stimmberechtigte
                )),
                ','.join((
                    '0',
                    '0',
                    '3204',  # BfsNrGemeinde
                    '10000',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'StimmenLeer',
                    'StimmenUngueltig',
                )),
                ','.join((
                    '3203',  # BfsNrGemeinde
                    '10000',  # Stimmberechtigte
                    '1200',  # Sperrung
                    '',  # StmAbgegeben
                    '',  # StmLeer
                    '1',  # StmUngueltig
                    '',  # StimmenLeer
                    '1',  # StimmenUngueltig
                )),
                ','.join((
                    '3204',  # BfsNrGemeinde
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
                    'Gewaehlt',
                    'Partei',
                )),
                ','.join((
                    '0',
                    '1',  # KNR
                    'xxx',  # Nachname
                    'xxx',  # Vorname
                    '',  # Gewaehlt
                    '',  # Partei
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '0',
                    '3203',  # BfsNrGemeinde
                    '1',  # KNR
                    '10',  # Stimmen
                )),
                ','.join((
                    '0',
                    '3204',  # BfsNrGemeinde
                    '1',  # KNR
                    '10',  # Stimmen
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    print_errors(errors)
    assert not errors

    # 1 Counted, 1 Uncounted, 75 Missing
    assert election.progress == (1, 77)


def test_import_wabstic_majorz_regional(session):
    session.add(
        Election(
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

        errors = import_election_wabstic_majorz(
            election, principal_zg, '0', '0',
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
                        'BfsNrGemeinde',
                        'Stimmberechtigte',
                    )),
                    ','.join((
                        '0',
                        '0',
                        '1701',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                    )),
                    ','.join((
                        '0',
                        '0',
                        '1702',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'BfsNrGemeinde',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'StimmenLeer',
                        'StimmenUngueltig',
                    )),
                    ','.join((
                        '1701',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                        '1200',  # Sperrung
                        '',  # StmAbgegeben
                        '',  # StmLeer
                        '1',  # StmUngueltig
                        '',  # StimmenLeer
                        '1',  # StimmenUngueltig
                    )),
                    ','.join((
                        '1702',  # BfsNrGemeinde
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
                        'Gewaehlt',
                        'Partei',
                    )),
                    ','.join((
                        '0',
                        '1',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                        '',  # Gewaehlt
                        '',  # Partei
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'BfsNrGemeinde',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        '0',
                        '1701',  # BfsNrGemeinde
                        '1',  # KNR
                        '10',  # Stimmen
                    )),
                    ','.join((
                        '0',
                        '1702',  # BfsNrGemeinde
                        '1',  # KNR
                        '10',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert [error.error for error in errors] == expected

        errors = import_election_wabstic_majorz(
            election, principal_sg, '0', '0',
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
                        'BfsNrGemeinde',
                        'Stimmberechtigte',
                    )),
                    ','.join((
                        '0',
                        '0',
                        '3231',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                    )),
                    ','.join((
                        '0',
                        '0',
                        '3276',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'BfsNrGemeinde',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'StimmenLeer',
                        'StimmenUngueltig',
                    )),
                    ','.join((
                        '3231',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                        '1200',  # Sperrung
                        '',  # StmAbgegeben
                        '',  # StmLeer
                        '1',  # StmUngueltig
                        '',  # StimmenLeer
                        '1',  # StimmenUngueltig
                    )),
                    ','.join((
                        '3276',  # BfsNrGemeinde
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
                        'Gewaehlt',
                        'Partei',
                    )),
                    ','.join((
                        '0',
                        '1',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                        '',  # Gewaehlt
                        '',  # Partei
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'BfsNrGemeinde',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        '0',
                        '3231',  # BfsNrGemeinde
                        '1',  # KNR
                        '10',  # Stimmen
                    )),
                    ','.join((
                        '0',
                        '3276',  # BfsNrGemeinde
                        '1',  # KNR
                        '10',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert [error.error for error in errors] == expected

    # OK
    election.distinct = True
    errors = import_election_wabstic_majorz(
        election, principal_zg, '0', '0',
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
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                )),
                ','.join((
                    '0',
                    '0',
                    '1701',  # BfsNrGemeinde
                    '10000',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'StimmenLeer',
                    'StimmenUngueltig',
                )),
                ','.join((
                    '1701',  # BfsNrGemeinde
                    '10000',  # Stimmberechtigte
                    '1200',  # Sperrung
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
                    'Gewaehlt',
                    'Partei',
                )),
                ','.join((
                    '0',
                    '1',  # KNR
                    'xxx',  # Nachname
                    'xxx',  # Vorname
                    '',  # Gewaehlt
                    '',  # Partei
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'BfsNrGemeinde',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '0',
                    '1701',  # BfsNrGemeinde
                    '1',  # KNR
                    '10',  # Stimmen
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert not errors
    assert election.progress == (1, 1)

    # Temporary
    for distinct, total in ((False, 1), (True, 13)):
        election.distinct = distinct

        errors = import_election_wabstic_majorz(
            election, principal_sg, '0', '0',
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
                        'BfsNrGemeinde',
                        'Stimmberechtigte',
                    )),
                    ','.join((
                        '0',
                        '0',
                        '3231',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'BfsNrGemeinde',
                        'Stimmberechtigte',
                        'Sperrung',
                        'StmAbgegeben',
                        'StmLeer',
                        'StmUngueltig',
                        'StimmenLeer',
                        'StimmenUngueltig',
                    )),
                    ','.join((
                        '3231',  # BfsNrGemeinde
                        '10000',  # Stimmberechtigte
                        '1200',  # Sperrung
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
                        'Gewaehlt',
                        'Partei',
                    )),
                    ','.join((
                        '0',
                        '1',  # KNR
                        'xxx',  # Nachname
                        'xxx',  # Vorname
                        '',  # Gewaehlt
                        '',  # Partei
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'SortGeschaeft',
                        'BfsNrGemeinde',
                        'KNR',
                        'Stimmen',
                    )),
                    ','.join((
                        '0',
                        '3231',  # BfsNrGemeinde
                        '1',  # KNR
                        '10',  # Stimmen
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert not errors
        assert election.progress == (1, total)
