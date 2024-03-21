from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.election_day.formats import import_election_wabstic_majorz
from onegov.election_day.models import Canton


def test_import_wabstic_majorz(session, import_test_datasets):

    election, errors = import_test_datasets(
        'wabstic',
        'election',
        'sg',
        'canton',
        election_type='majorz',
        number_of_mandates=6,
        date_=date(2016, 2, 28),
        dataset_name='regierungsratswahlen-2016',
        has_expats=True,
        election_number='9',
        election_district='1'
    )

    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (78, 78)
    assert len(election.results) == 78
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


def test_import_wabstic_intermediate(session, import_test_datasets):

    election, errors = import_test_datasets(
        'wabstic',
        'election',
        'sg',
        'canton',
        election_type='majorz',
        number_of_mandates=1,
        date_=date(2022, 3, 12),
        dataset_name='staenderatswahlen-2022-intermediate',
        has_expats=True,
        election_number='1',
        election_district='1'
    )

    assert not errors
    assert election.last_result_change
    assert not election.completed
    assert election.progress == (1, 78)
    assert len(election.results) == 78
    assert election.absolute_majority == 0
    assert election.eligible_voters == 5000
    assert election.received_ballots == 1820
    assert election.accounted_ballots == 1790
    assert election.blank_ballots == 10
    assert election.invalid_ballots == 20
    assert election.accounted_votes == 1790
    assert election.allocated_mandates == 0
    assert election.elected_candidates == []
    assert sum((c.votes for c in election.candidates)) == 1790


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
        ('wm_wahl', "Missing columns: 'absolutesmehr, anzpendentgde'"),
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
                    'AnzPendendGde'
                )),
                ','.join((
                    '0',
                    'xxx',  # AbsolutesMehr
                    '4',  # Ausmittlungsstand
                    '1'
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

    for has_expats in (False, True):
        election.has_expats = has_expats
        for entity_id in ('9170', '0'):
            errors = import_election_wabstic_majorz(
                election, principal, '0', '0',
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'SortGeschaeft',
                            'AbsolutesMehr',
                            'Ausmittlungsstand',
                            'AnzPendendGde'
                        )),
                        ','.join((
                            '0',
                            '5000',  # AbsolutesMehr
                            '0',  # Ausmittlungsstand
                            '1'
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
                            '1234',  # Sperrung
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
            result = next(
                (r for r in election.results if r.entity_id == 0), None
            )
            if has_expats:
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
                    'AnzPendendGde'
                )),
                ','.join((
                    '0',
                    '5000',  # AbsolutesMehr
                    '0',  # Ausmittlungsstand
                    '1'
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
    assert not errors

    # 1 Counted, 1 Uncounted, 75 Missing
    assert election.progress == (1, 77)


def test_import_wabstic_majorz_regional(session):

    def create_csv(results):
        lines_wm_wahl = []
        lines_wm_wahl.append((
            'SortGeschaeft',
            'AbsolutesMehr',
            'Ausmittlungsstand',
            'AnzPendendGde'
        ))
        lines_wm_wahl.append((
            '0',  # SortGeschaeft
            '5000',  # AbsolutesMehr
            '0',  # Ausmittlungsstand
            '1'  # AnzPendendGde
        ))

        lines_wmstatic_gemeinden = []
        lines_wmstatic_gemeinden.append((
            'SortWahlkreis',
            'SortGeschaeft',
            'BfsNrGemeinde',
            'Stimmberechtigte',
        ))
        for entity_id, counted in results:
            lines_wmstatic_gemeinden.append((
                '0',  # SortWahlkreis
                '0',  # SortGeschaeft
                str(entity_id),  # BfsNrGemeinde
                '10000',  # Stimmberechtigte
            ))

        lines_wm_gemeinden = []
        lines_wm_gemeinden.append((
            'BfsNrGemeinde',
            'Stimmberechtigte',
            'Sperrung',
            'StmAbgegeben',
            'StmLeer',
            'StmUngueltig',
            'StimmenLeer',
            'StimmenUngueltig',
        ))
        for entity_id, counted in results:
            lines_wm_gemeinden.append((
                str(entity_id),  # BfsNrGemeinde
                '10000',  # Stimmberechtigte
                '1200' if counted else '',  # Sperrung
                '',  # StmAbgegeben
                '',  # StmLeer
                '1',  # StmUngueltig
                '',  # StimmenLeer
                '1',  # StimmenUngueltig
            ))

        lines_wm_kandidaten = []
        lines_wm_kandidaten.append((
            'SortGeschaeft',
            'KNR',
            'Nachname',
            'Vorname',
            'Gewaehlt',
            'Partei',
        ))
        lines_wm_kandidaten.append((
            '0',  # SortGeschaeft
            '1',  # KNR
            'xxx',  # Nachname
            'xxx',  # Vorname
            '',  # Gewaehlt
            '',  # Partei
        ))

        lines_wm_kandidatengde = []
        lines_wm_kandidatengde.append((
            'SortGeschaeft',
            'BfsNrGemeinde',
            'KNR',
            'Stimmen',
        ))
        for entity_id, counted in results:
            lines_wm_kandidatengde.append((
                '0',  # SortGeschaeft
                str(entity_id),  # BfsNrGemeinde
                '1',  # KNR
                '10',  # Stimmen
            ))

        return (
            '0', '0',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in lines_wm_wahl
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in lines_wmstatic_gemeinden
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in lines_wm_gemeinden
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in lines_wm_kandidaten
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in lines_wm_kandidatengde
                ).encode('utf-8')
            ), 'text/plain'
        )

    session.add(
        Election(
            title='election',
            domain='region',
            date=date(2022, 2, 19),
            number_of_mandates=1
        )
    )
    session.flush()
    election = session.query(Election).one()

    # ZG, municipality, too many municipalitites
    principal = Canton(canton='zg')
    election.domain = 'municipality'
    election.domain_segment = 'Baar'
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv(((1701, False), (1702, False)))
    )
    assert '1702 is not part of this business' in [
        (e.error.interpolate()) for e in errors
    ]

    # ZG, municipality, ok
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv(((1701, False),))
    )
    assert not errors
    assert election.progress == (0, 1)

    # ZG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv(((1701, True), (1702, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # SG, district, too many districts
    principal = Canton(canton='sg')
    election.domain = 'district'
    election.domain_segment = 'Werdenberg'
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv(((3271, False), (3201, False)))
    )
    assert '3201 is not part of Werdenberg' in [
        (e.error.interpolate()) for e in errors
    ]

    # SG, district, ok
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv((
            (3271, True), (3272, False), (3273, False), (3274, False),
            # (3275, False), (3276, False)
        ))
    )
    assert not errors
    assert election.progress == (1, 6)

    # SG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv(((3271, True), (3201, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # GR, region, too many regions
    principal = Canton(canton='gr')
    election.domain = 'region'
    election.domain_segment = 'Ilanz'
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert '3513 is not part of Ilanz' in [
        (e.error.interpolate()) for e in errors
    ]

    # GR, region, ok
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv((
            (3572, True), (3575, False), (3581, False), (3582, False)
            # (3619, False), (3988, False)
        ))
    )
    assert not errors
    assert election.progress == (1, 6)

    # GR, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_wabstic_majorz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert not errors
    assert election.progress == (1, 2)
