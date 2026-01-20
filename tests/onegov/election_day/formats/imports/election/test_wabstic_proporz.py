from __future__ import annotations

from datetime import date
from io import BytesIO
from onegov.election_day.formats import import_election_wabstic_proporz
from onegov.election_day.formats.imports.election.wabstic_proporz import (
    get_list_id_from_knr)
from onegov.election_day.models import Canton
from onegov.election_day.models import Election
from onegov.election_day.models import ProporzElection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from tests.onegov.election_day.conftest import ImportTestDatasets


def test_get_list_id_from_knr() -> None:

    DummyLine: Any

    class DummyLine:  # type: ignore[no-redef]
        def __init__(self, knr: str) -> None:
            self.knr = knr
    # position on the list is always two numbers value
    # 05a.01 and 0501 can never be in the same vote
    assert get_list_id_from_knr(DummyLine('0101')) == '01'
    assert get_list_id_from_knr(DummyLine('50.05')) == '50'
    assert get_list_id_from_knr(DummyLine('05a.01')) == '05a'
    assert get_list_id_from_knr(DummyLine('05a.1')) == '05a'


def test_import_wabstic_proporz_cantonal(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:

    # - cantonal results from SG from the 18.10.2015 (Nationalrat)

    results = import_test_datasets(
        'wabstic',
        'election',
        'sg',
        domain='canton',
        election_type='proporz',
        dataset_name='nationalratswahl-2015',
        number_of_mandates=12,
        date_=date(2015, 10, 18),
        has_expats=True,
    )

    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors
    assert election.last_result_change
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
        for l in election.lists
        if l.number_of_mandates > 0
    ]) == [('CVP', 3), ('FDP', 2), ('SP', 2), ('SVP', 5)]
    list_ = next((l for l in election.lists if l.name == 'SVP'))
    assert list_.votes == 620183

    assert sorted((c.votes for c in election.list_connections))[-1] == 636317


def test_import_wabstic_proporz_regional_sg(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    for number, district, segment, mandates, entities, votes, turnout in (
        ('1', '1', 'St. Gallen', 29, 9, 949454, 44.45),
        ('2', '2', 'Rorschach', 10, 9, 105959, 43.07),
        ('3', '3', 'Rheintal', 17, 13, 318662, 46.86),
        ('4', '5', 'Werdenberg', 9, 6, 83098, 43.94),
        ('5', '6', 'Sarganserland', 10, 8, 119157, 48.10),
        ('6', '7', 'See-Gaster', 16, 10, 301843, 44.65),
        ('7', '8', 'Toggenburg', 11, 12, 159038, 49.15),
        ('8', '13', 'Wil', 18, 10, 352595, 43.94),
    ):
        results = import_test_datasets(
            'wabstic',
            'election',
            'sg',
            domain='district',
            domain_segment=segment,
            election_type='proporz',
            number_of_mandates=mandates,
            dataset_name='kantonsratswahl-2016',
            election_number=number,
            election_district=district
        )

        assert len(results) == 1
        election, errors = next(iter(results.values()))
        assert not errors
        assert election.last_result_change
        assert election.completed
        assert election.progress == (entities, entities)
        assert election.accounted_votes == votes
        assert round(election.turnout, 2) == turnout


def test_import_wabstic_proporz_missing_headers(session: Session) -> None:
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
    assert isinstance(election, ProporzElection)
    principal = Canton(canton='sg')

    errors = import_election_wabstic_proporz(
        election, principal, '0', '0',
        BytesIO('Ausmittlungsstand,\n'.encode('utf-8')), 'text/plain',
        BytesIO((  # wpstatic_gemeinden
            '\n'.join((
                ','.join((
                    'SortWahlkreis',
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_gemeinden
            '\n'.join((
                ','.join((
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'AnzWZAmtLeer',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_listen
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
        BytesIO((  # wp_listengde
            '\n'.join((
                ','.join((
                    'ListNr',
                    'StimmenTotal',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wpstatic_kandidaten
            '\n'.join((
                ','.join((
                    'KNR',
                    'Nachname',
                    'Vorname',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_kandidaten
            '\n'.join((
                ','.join((
                    'KNR',
                    'Gewaehlt',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_kandidatengde
            '\n'.join((
                ','.join((
                    'KNR',
                    'Stimmen',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert sorted([(e.filename, e.error.interpolate()) for e in errors]) == [  # type: ignore[attr-defined]
        ('wp_gemeinden', "Missing columns: 'bfsnrgemeinde'"),
        ('wp_kandidaten', "Missing columns: 'sortgeschaeft'"),
        ('wp_kandidatengde', "Missing columns: 'bfsnrgemeinde'"),
        ('wp_listen', "Missing columns: 'sortgeschaeft'"),
        ('wp_listengde', "Missing columns: 'bfsnrgemeinde'"),
        ('wp_wahl', "Missing columns: 'sortgeschaeft, anzpendentgde'"),
        ('wpstatic_gemeinden', "Missing columns: 'sortgeschaeft'"),
        ('wpstatic_kandidaten', "Missing columns: 'sortgeschaeft'"),
    ]


def test_import_wabstic_proporz_invalid_values(session: Session) -> None:
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
    assert isinstance(election, ProporzElection)
    principal = Canton(canton='sg')

    errors = import_election_wabstic_proporz(
        election, principal, '0', '0',
        BytesIO((       # wp_wahl
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                    'AnzPendentGde'
                )),
                ','.join((
                    '0',
                    '4',  # Ausmittlungsstand
                    '1'
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((       # wpstatic_gemeinden
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
        BytesIO((       # wp_gemeinden
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'AnzWZAmtLeer',
                )),
                ','.join((
                    '3215',  # BfsNrGemeinde
                    'xxx',  # Stimmberechtigte
                    'xxx',  # Sperrung
                    'xxx',  # StmAbgegeben
                    'xxx',  # StmLeer
                    'xxx',  # StmUngueltig
                    'xxx',  # AnzWZAmtLeer
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((       # wp_listen
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
        BytesIO((       # wp_listengde
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'ListNr',
                    'StimmenTotal',
                )),
                ','.join((
                    '100',  # BfsNrGemeinde
                    'xxx',  # ListNr
                    'xxx',  # StimmenTotal
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((       # wp_wahl
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
        BytesIO((       # wpstatic_gemeinden
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'KNR',
                    'Gewaehlt',
                )),
                ','.join((
                    '0',
                    'xxx',  # KNR
                    'xxx',  # Gewaehlt
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((       # wp_static_kandidaten
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '100',  # BfsNrGemeinde
                    'xxx',  # KNR
                    'xxx',  # Stimmen
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors  # type: ignore[attr-defined]
    ]) == [
        ('wp_gemeinden', 2, 'Invalid integer: sperrung'),
        ('wp_gemeinden', 2, 'Invalid integer: stimmberechtigte'),
        ('wp_gemeinden', 2, 'Invalid integer: stmabgegeben'),
        ('wp_kandidaten', 2, 'Invalid integer: gewaehlt'),
        ('wp_kandidatengde', 2, 'Invalid integer: stimmen'),
        ('wp_listen', 2, 'Invalid integer: sitze'),
        ('wp_listengde', 2, 'Invalid integer: stimmentotal'),
        ('wpstatic_gemeinden', 2, '100 is unknown'),
        ('wpstatic_kandidaten', 2, 'List_id x has not been found'
                                   ' in list numbers')
    ]


def test_import_wabstic_proporz_expats(session: Session) -> None:
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
    assert isinstance(election, ProporzElection)
    principal = Canton(canton='sg')

    for has_expats in (False, True):
        election.has_expats = has_expats
        for entity_id in ('9170', '0'):
            raw_errors = import_election_wabstic_proporz(
                election, principal, '0', '0',
                BytesIO((  # wp_wahl
                    '\n'.join((
                        ','.join((
                            'SortGeschaeft',
                            'Ausmittlungsstand',
                            'AnzPendentGde'
                        )),
                        ','.join((
                            '0',
                            '0',  # Ausmittlungsstand
                            '1'
                        )),
                    ))
                ).encode('utf-8')), 'text/plain',
                BytesIO((  # wpstatic_gemeinden
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
                            '',  # Stimmberechtigte
                        )),
                    ))
                ).encode('utf-8')), 'text/plain',
                BytesIO((  # wp_gemeinden
                    '\n'.join((
                        ','.join((
                            'BfsNrGemeinde',
                            'Stimmberechtigte',
                            'Sperrung',
                            'StmAbgegeben',
                            'StmLeer',
                            'StmUngueltig',
                            'AnzWZAmtLeer',
                        )),
                        ','.join((
                            entity_id,  # BfsNrGemeinde
                            '10000',  # Stimmberechtigte
                            '10',  # Sperrung
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
                            'BfsNrGemeinde',
                            'ListNr',
                            'StimmenTotal',
                        )),
                        ','.join((
                            entity_id,  # BfsNrGemeinde
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
                            'Gewaehlt',
                        )),
                        ','.join((
                            '0',
                            '101',  # KNR
                            '',  # Gewaehlt
                        )),
                    ))
                ).encode('utf-8')), 'text/plain',
                BytesIO((  # wp_kandidatengde
                    '\n'.join((
                        ','.join((
                            'BfsNrGemeinde',
                            'KNR',
                            'Stimmen',
                        )),
                        ','.join((
                            entity_id,  # BfsNrGemeinde
                            '101',  # KNR
                            '100',  # Stimmen
                        )),
                    ))
                ).encode('utf-8')), 'text/plain'
            )
            errors = [(e.line, e.error.interpolate()) for e in raw_errors]  # type: ignore[attr-defined]
            result = next(
                (r for r in election.results if r.entity_id == 0), None
            )
            if has_expats:
                assert errors == []
                assert result is not None
                assert result.blank_ballots == 1
            else:
                assert errors == []
                assert result is None


def test_import_wabstic_proporz_temporary_results(session: Session) -> None:
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
    assert isinstance(election, ProporzElection)
    principal = Canton(canton='sg')

    errors = import_election_wabstic_proporz(
        election, principal, '0', '0',
        BytesIO((  # wp_wahl
            '\n'.join((
                ','.join((
                    'SortGeschaeft',
                    'Ausmittlungsstand',
                    'AnzPendentGde'
                )),
                ','.join((
                    '0',
                    '0',  # Ausmittlungsstand
                    '1'
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wpstatic_gemeinden
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
                    '',  # Stimmberechtigte
                )),
                ','.join((
                    '0',
                    '0',
                    '3204',  # BfsNrGemeinde
                    '',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_gemeinden
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'Stimmberechtigte',
                    'Sperrung',
                    'StmAbgegeben',
                    'StmLeer',
                    'StmUngueltig',
                    'AnzWZAmtLeer',
                )),
                ','.join((
                    '3203',  # BfsNrGemeinde
                    '10000',  # Stimmberechtigte
                    '1200',  # Sperrung
                    '',  # StmAbgegeben
                    '1',  # StmLeer
                    '',  # StmUngueltig
                    '',  # AnzWZAmtLeer
                )),
                ','.join((
                    '3204',  # BfsNrGemeinde
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
                    'BfsNrGemeinde',
                    'ListNr',
                    'StimmenTotal',
                )),
                ','.join((
                    '3203',  # BfsNrGemeinde
                    '1',  # ListNr
                    '0',  # StimmenTotal
                )),
                ','.join((
                    '3204',  # BfsNrGemeinde
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
                    'Gewaehlt',
                )),
                ','.join((
                    '0',
                    '101',  # KNR
                    '',  # Gewaehlt
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((  # wp_kandidatengde
            '\n'.join((
                ','.join((
                    'BfsNrGemeinde',
                    'KNR',
                    'Stimmen',
                )),
                ','.join((
                    '3203',  # BfsNrGemeinde
                    '101',  # KNR
                    '100',  # Stimmen
                )),
                ','.join((
                    '3204',  # BfsNrGemeinde
                    '101',  # KNR
                    '100',  # Stimmen
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert not errors

    # 1 Counted, 1 Uncounted, 75 Missing
    assert election.progress == (1, 77)


def test_import_wabstic_proporz_regional(session: Session) -> None:

    def create_csv(results: tuple[tuple[int, bool], ...]) -> tuple[
        str, str,
        BytesIO, str,
        BytesIO, str,
        BytesIO, str,
        BytesIO, str,
        BytesIO, str,
        BytesIO, str,
        BytesIO, str,
        BytesIO, str,
    ]:
        lines_wm_wahl = []
        lines_wm_wahl.append((
            'SortGeschaeft',
            'Ausmittlungsstand',
            'AnzPendendGde'
        ))
        lines_wm_wahl.append((
            '0',  # SortGeschaeft
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
            'AnzWZAmtLeer',
        ))
        for entity_id, counted in results:
            lines_wm_gemeinden.append((
                str(entity_id),  # BfsNrGemeinde
                '10000',  # Stimmberechtigte
                '1200' if counted else '',  # Sperrung
                '',  # StmAbgegeben
                '1',  # StmLeer
                '',  # StmUngueltig
                '',  # AnzWZAmtLeer
            ))

        lines_wp_listen = []
        lines_wp_listen.append((
            'SortGeschaeft',
            'ListNr',
            'ListCode',
            'Sitze',
            'ListVerb',
            'ListUntVerb',
        ))
        lines_wp_listen.append((
            '0',  # SortGeschaeft
            '1',  # ListNr
            '1',  # ListCode
            '',  # Sitze
            '',  # ListVerb
            '',  # ListUntVerb
        ))

        wp_listengde = []
        wp_listengde.append((
            'BfsNrGemeinde',
            'ListNr',
            'StimmenTotal',
        ))
        for entity_id, counted in results:
            wp_listengde.append((
                str(entity_id),  # BfsNrGemeinde
                '1',  # ListNr
                '0',  # StimmenTotal
            ))

        lines_wpstatic_kandidaten = []
        lines_wpstatic_kandidaten.append((
            'SortGeschaeft',
            'KNR',
            'Nachname',
            'Vorname',
        ))
        lines_wpstatic_kandidaten.append((
            '0',  # SortGeschaeft
            '101',  # KNR
            'xxx',  # Nachname
            'xxx',  # Vorname
        ))

        wp_kandidaten = []
        wp_kandidaten.append((
            'SortGeschaeft',
            'KNR',
            'Gewaehlt',
        ))
        wp_kandidaten.append((
            '0',
            '101',  # KNR
            '',  # Gewaehlt
        ))

        lines_wp_kandidatengde = []
        lines_wp_kandidatengde.append((
            'BfsNrGemeinde',
            'KNR',
            'Stimmen',
        ))
        for entity_id, counted in results:
            lines_wp_kandidatengde.append((
                str(entity_id),  # BfsNrGemeinde
                '101',  # KNR
                '100',  # Stimmen

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
                    (','.join(c for c in l)) for l in lines_wp_listen
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in wp_listengde
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in lines_wpstatic_kandidaten
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in wp_kandidaten
                ).encode('utf-8')
            ), 'text/plain',
            BytesIO(
                '\n'.join(
                    (','.join(c for c in l)) for l in lines_wp_kandidatengde
                ).encode('utf-8')
            ), 'text/plain'
        )

    session.add(
        ProporzElection(
            title='election',
            domain='region',
            date=date(2022, 2, 19),
            number_of_mandates=1
        )
    )
    session.flush()
    election = session.query(Election).one()
    assert isinstance(election, ProporzElection)

    # ZG, municipality, too many municipalitites
    principal = Canton(canton='zg')
    election.domain = 'municipality'
    election.domain_segment = 'Baar'
    errors = import_election_wabstic_proporz(
        election, principal,
        *create_csv(((1701, False), (1702, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '1702 is not part of this business'
    ]

    # ZG, municipality, ok
    errors = import_election_wabstic_proporz(
        election, principal,
        *create_csv(((1701, False),))
    )
    assert not errors
    assert election.progress == (0, 1)

    # ZG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_wabstic_proporz(
        election, principal,
        *create_csv(((1701, True), (1702, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # SG, district, too many districts
    principal = Canton(canton='sg')
    election.domain = 'district'
    election.domain_segment = 'Werdenberg'
    errors = import_election_wabstic_proporz(
        election, principal,
        *create_csv(((3271, False), (3201, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '3201 is not part of Werdenberg'
    ]

    # SG, district, ok
    errors = import_election_wabstic_proporz(
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
    errors = import_election_wabstic_proporz(
        election, principal,
        *create_csv(((3271, True), (3201, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # GR, region, too many regions
    principal = Canton(canton='gr')
    election.domain = 'region'
    election.domain_segment = 'Ilanz'
    errors = import_election_wabstic_proporz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '3513 is not part of Ilanz'
    ]

    # GR, region, ok
    errors = import_election_wabstic_proporz(
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
    errors = import_election_wabstic_proporz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert not errors
    assert election.progress == (1, 2)
