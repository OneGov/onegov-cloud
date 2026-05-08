from __future__ import annotations

from datetime import date
from decimal import Decimal
from freezegun import freeze_time
from lxml import etree
from onegov.core.templates import PageTemplate
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.screen_widgets import (
    CountedEntitiesWidget,
    ElectionCompoundCandidatesTableWidget,
    ElectionCompoundDistrictsMapWidget,
    ElectionCompoundDistrictsTableWidget,
    ElectionCompoundListGroupsChartWidget,
    ElectionCompoundListGroupsTableWidget,
    ElectionCompoundPartyStrengthsChartWidget,
    ElectionCompoundPartyStrengthsTableWidget,
    ElectionCompoundSeatAllocationChartWidget,
    ElectionCompoundSeatAllocationTableWidget,
    ElectionCompoundSuperregionsMapWidget,
    ElectionCompoundSuperregionsTableWidget,
    IfCompletedWidget,
    IfNotCompletedWidget,
    LastResultChangeWidget,
    ModelProgressWidget,
    ModelTitleWidget,
    NumberOfCountedEntitiesWidget,
    TotalEntitiesWidget,
)
from tests.onegov.election_day.common import DummyRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.widgets import Widget
    from ..conftest import ImportTestDatasets, TestApp


def test_election_compound_widgets(
    election_day_app_sg: TestApp,
    import_test_datasets: ImportTestDatasets
) -> None:

    structure = """
        <model-title class="class-for-title"/>
        <model-progress class="class-for-progress"/>
        <counted-entities class="class-for-counted-entities"/>
        <election-compound-candidates-table
            class="class-for-candidates-table"/>
        <election-compound-districts-table
            class="class-for-districts-table"/>
        <election-compound-districts-map
            class="class-for-districts-map"/>
        <election-compound-list-groups-table
            class="class-for-list-groups-table"/>
        <election-compound-list-groups-chart
            class="class-for-list-groups-chart"/>
        <number-of-counted-entities
            class="class-for-number-of-counted-entities"/>
        <total-entities class="class-for-total-entities"/>
        <last-result-change class="class-for-last-result-change"/>
        <election-compound-seat-allocation-table
            class="class-for-seat-allocation-table"/>
        <election-compound-seat-allocation-chart
            class="class-for-seat-allocation-chart"/>
        <election-compound-superregions-table
            class="class-for-superregions-table"/>
        <election-compound-superregions-map
            class="class-for-superregions-map"/>
        <if-completed>is-completed</if-completed>
        <if-not-completed>is-not-completed</if-not-completed>
        <election-compound-party-strengths-chart
            class="class-for-party-strengths-chart-1"
            horizontal="true"/>
        <election-compound-party-strengths-chart
            class="class-for-party-strengths-chart-2"
            horizontal="false"/>
        <election-compound-party-strengths-table
            class="class-for-party-strengths-table-1"/>
        <election-compound-party-strengths-table
            class="class-for-party-strengths-table-2"
            year="2019"/>
    """
    widgets: list[Widget] = [
        CountedEntitiesWidget(),
        ElectionCompoundCandidatesTableWidget(),
        ElectionCompoundDistrictsMapWidget(),
        ElectionCompoundDistrictsTableWidget(),
        ElectionCompoundListGroupsChartWidget(),
        ElectionCompoundListGroupsTableWidget(),
        ElectionCompoundPartyStrengthsChartWidget(),
        ElectionCompoundPartyStrengthsTableWidget(),
        ElectionCompoundSeatAllocationChartWidget(),
        ElectionCompoundSeatAllocationTableWidget(),
        ElectionCompoundSuperregionsMapWidget(),
        ElectionCompoundSuperregionsTableWidget(),
        IfCompletedWidget(),
        IfNotCompletedWidget(),
        LastResultChangeWidget(),
        ModelProgressWidget(),
        ModelTitleWidget(),
        NumberOfCountedEntitiesWidget(),
        TotalEntitiesWidget(),
    ]

    # Empty
    session = election_day_app_sg.session()
    session.add(
        ElectionCompound(
            title='Compound', domain='canton', date=date(2020, 3, 8),
            pukelsheim=True, completes_manually=True, voters_counts=True,
            exact_voters_counts=True
        )
    )
    model = session.query(ElectionCompound).one()
    request: Any = DummyRequest(app=election_day_app_sg, session=session)
    layout = ElectionCompoundLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'districts': {},
        'elected_candidates': [],
        'election': model,
        'election_compound': model,
        'embed': False,
        'entities': '',
        'groups': [],
        'layout': layout,
        'model': model,
        'request': request,
        'seat_allocations': [],
        'superregions': {},
        'party_years': [],
        'party_deltas': False,
        'party_results': {}
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Compound</span>' in result
    assert 'ElectionCompound/by-district' in result
    assert 'ElectionCompound/by-superregion' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert 'class-for-title' in result
    assert 'class-for-progress' in result
    assert 'class-for-counted-entities' in result
    assert 'class-for-candidates-table' in result
    assert 'class-for-districts-table' in result
    assert 'class-for-districts-map' in result
    assert 'class-for-list-groups-table' in result
    assert 'class-for-list-groups-chart' in result
    assert 'class-for-number-of-counted-entities' in result
    assert 'class-for-total-entities' in result
    assert 'class-for-last-result-change' in result
    assert 'class-for-seat-allocation-table' in result
    assert 'class-for-seat-allocation-chart' in result
    assert 'class-for-superregions-table' in result
    assert 'class-for-superregions-map' in result
    assert 'class-for-party-strengths-chart-1' in result
    assert 'class-for-party-strengths-chart-2' in result
    assert 'class-for-party-strengths-table-1' in result
    assert 'class-for-party-strengths-table-2' in result

    # Add intermediate results
    with freeze_time('2022-01-01 12:00'):
        results = import_test_datasets(
            'internal',
            'election',
            'sg',
            'district',
            'proporz',
            date_=date(2020, 3, 8),
            number_of_mandates=17,
            domain_segment='Rheintal',
            dataset_name=(
                'kantonsratswahl-2020-wahlkreis-rheintal-intermediate'
            ),
            app_session=session
        )
        assert len(results) == 1
        election_1, errors = next(iter(results.values()))
        assert not errors
        results = import_test_datasets(
            'internal',
            'election',
            'sg',
            'district',
            'proporz',
            date_=date(2020, 3, 8),
            number_of_mandates=10,
            domain_segment='Rorschach',
            dataset_name='kantonsratswahl-2020-wahlkreis-rorschach',
            app_session=session
        )
        assert len(results) == 1
        election_2, errors = next(iter(results.values()))
        assert not errors
        session.add(election_1)
        session.add(election_2)
        model.elections = [election_1, election_2]
        session.flush()

    layout = ElectionCompoundLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    e_1 = election_1.title
    e_2 = election_2.title
    assert data == {
        'districts': {
            e_1: ('Rheintal', f'ProporzElection/{e_1}', ''),
            e_2: ('Rorschach', f'ProporzElection/{e_2}', '')
        },
        'elected_candidates': [
            ('Bruss-Schmidheiny', 'Carmen', '', None, None, 'SVP', '01', e_1),
            ('Eugster', 'Thomas', '', None, None, 'SVP', '01', e_1),
            ('Freund', 'Walter', '', None, None, 'SVP', '01', e_1),
            ('Götte', 'Michael', '', None, None, 'SVP', '01', e_2),
            ('Kuster', 'Peter', '', None, None, 'SVP', '01', e_1),
            ('Luterbacher', 'Mäge', '', None, None, 'SVP', '01', e_2),
            ('Wasserfallen', 'Sandro', '', None, None, 'SVP', '01', e_2),
            ('Willi', 'Christian', '', None, None, 'SVP', '01', e_1),
            ('Wüst', 'Markus', '', None, None, 'SVP', '01', e_1),
            ('Broger', 'Andreas', '', None, None, 'CVP', '02', e_1),
            ('Dürr', 'Patrick', '', None, None, 'CVP', '02', e_1),
            ('Hess', 'Sandro', '', None, None, 'CVP', '02', e_1),
            ('Schöbi', 'Michael', '', None, None, 'CVP', '02', e_1),
            ('Frei', 'Raphael', '', None, None, 'FDP', '02a', e_2),
            ('Raths', 'Robert', '', None, None, 'FDP', '02a', e_2),
            ('Britschgi', 'Stefan', '', None, None, 'FDP', '03', e_1),
            ('Graf', 'Claudia', '', None, None, 'FDP', '03', e_1),
            ('Huber', 'Rolf', '', None, None, 'FDP', '03', e_1),
            ('Bucher', 'Laura', '', None, None, 'SP', '04', e_1),
            ('Gemperli', 'Dominik', '', None, None, 'CVP', '04', e_2),
            ('Krempl-Gnädinger', 'Luzia', '', None, None, 'CVP', '04', e_2),
            ('Maurer', 'Remo', '', None, None, 'SP', '04', e_1),
            ('Etterlin', 'Guido', '', None, None, 'SP', '05', e_2),
            ('Gschwend', 'Meinrad', '', None, None, 'GRÜ', '05', e_1),
            ('Schöb', 'Andrea', '', None, None, 'SP', '05', e_2),
            ('Losa', 'Jeannette', '', None, None, 'GRÜ', '06', e_2),
            ('Mattle', 'Ruedi', '', None, None, 'GLP', '06', e_1)
        ],
        'election': model,
        'election_compound': model,
        'embed': False,
        'entities': '',
        'groups': [],
        'layout': layout,
        'model': model,
        'request': request,
        'seat_allocations': [],
        'superregions': {},
        'party_years': [],
        'party_deltas': False,
        'party_results': {}
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Compound</span>' in result
    assert '0 of 2' in result
    assert f'<div>{e_2}</div>'
    assert 'election-compound-candidates-table' in result
    assert 'Bruss-Schmidheiny Carmen' in result
    assert 'election-compound-districts-table' in result
    assert '0 of 10' in result
    assert '9 of 9' in result
    assert '0 of 17' in result
    assert '1 of 13' in result
    assert '0' in result
    assert '2' in result
    assert '01.01.2022' in result
    assert 'election-compound-superregions-table' in result
    assert 'ElectionCompound/by-district' in result
    assert 'ElectionCompound/by-superregion' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert (
        'data-dataurl="ElectionCompound/party-strengths-data?horizontal=True"'
    ) in result
    assert (
        'data-dataurl="ElectionCompound/party-strengths-data?horizontal=False"'
    ) in result
    assert 'tab-navigation' not in result
    assert 'tabs-content' not in result
    assert 'class-for-title' in result
    assert 'class-for-progress' in result
    assert 'class-for-counted-entities' in result
    assert 'class-for-candidates-table' in result
    assert 'class-for-districts-table' in result
    assert 'class-for-districts-map' in result
    assert 'class-for-list-groups-table' in result
    assert 'class-for-list-groups-chart' in result
    assert 'class-for-number-of-counted-entities' in result
    assert 'class-for-total-entities' in result
    assert 'class-for-last-result-change' in result
    assert 'class-for-seat-allocation-table' in result
    assert 'class-for-seat-allocation-chart' in result
    assert 'class-for-superregions-table' in result
    assert 'class-for-superregions-map' in result
    assert 'class-for-party-strengths-chart-1' in result
    assert 'class-for-party-strengths-chart-2' in result
    assert 'class-for-party-strengths-table-1' in result
    assert 'class-for-party-strengths-table-2' in result

    # Add final results
    with freeze_time('2022-01-02 12:00'):
        results = import_test_datasets(
            'internal',
            'election',
            'sg',
            'district',
            'proporz',
            date_=date(2020, 3, 8),
            domain_segment='Rheintal',
            number_of_mandates=17,
            dataset_name='kantonsratswahl-2020-wahlkreis-rheintal',
            app_session=session
        )
        assert len(results) == 1
        election_1, errors = next(iter(results.values()))
        assert not errors
        results_ = import_test_datasets(
            'internal',
            'parties',
            'sg',
            'district',
            election=model,
            dataset_name='kantonsratswahl-2020-parteien',
        )
        assert len(results) == 1
        errors_ = next(iter(results_.values()))
        assert not errors_
        session.add(election_1)
        model.elections = [election_1, election_2]
        model.manually_completed = True
        session.flush()

    layout = ElectionCompoundLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    e_1 = election_1.title
    e_2 = election_2.title
    data['groups'] = [
        (r.name, r.voters_count, r.number_of_mandates) for r in data['groups']
    ]
    assert data == {
        'districts': {
            e_1: ('Rheintal', f'ProporzElection/{e_1}', ''),
            e_2: ('Rorschach', f'ProporzElection/{e_2}', '')
        },
        'elected_candidates': [
            ('Bruss-Schmidheiny', 'Carmen', '', None, None, 'SVP', '01', e_1),
            ('Eugster', 'Thomas', '', None, None, 'SVP', '01', e_1),
            ('Freund', 'Walter', '', None, None, 'SVP', '01', e_1),
            ('Götte', 'Michael', '', None, None, 'SVP', '01', e_2),
            ('Kuster', 'Peter', '', None, None, 'SVP', '01', e_1),
            ('Luterbacher', 'Mäge', '', None, None, 'SVP', '01', e_2),
            ('Wasserfallen', 'Sandro', '', None, None, 'SVP', '01', e_2),
            ('Willi', 'Christian', '', None, None, 'SVP', '01', e_1),
            ('Wüst', 'Markus', '', None, None, 'SVP', '01', e_1),
            ('Broger', 'Andreas', '', None, None, 'CVP', '02', e_1),
            ('Dürr', 'Patrick', '', None, None, 'CVP', '02', e_1),
            ('Hess', 'Sandro', '', None, None, 'CVP', '02', e_1),
            ('Schöbi', 'Michael', '', None, None, 'CVP', '02', e_1),
            ('Frei', 'Raphael', '', None, None, 'FDP', '02a', e_2),
            ('Raths', 'Robert', '', None, None, 'FDP', '02a', e_2),
            ('Britschgi', 'Stefan', '', None, None, 'FDP', '03', e_1),
            ('Graf', 'Claudia', '', None, None, 'FDP', '03', e_1),
            ('Huber', 'Rolf', '', None, None, 'FDP', '03', e_1),
            ('Bucher', 'Laura', '', None, None, 'SP', '04', e_1),
            ('Gemperli', 'Dominik', '', None, None, 'CVP', '04', e_2),
            ('Krempl-Gnädinger', 'Luzia', '', None, None, 'CVP', '04', e_2),
            ('Maurer', 'Remo', '', None, None, 'SP', '04', e_1),
            ('Etterlin', 'Guido', '', None, None, 'SP', '05', e_2),
            ('Gschwend', 'Meinrad', '', None, None, 'GRÜ', '05', e_1),
            ('Schöb', 'Andrea', '', None, None, 'SP', '05', e_2),
            ('Losa', 'Jeannette', '', None, None, 'GRÜ', '06', e_2),
            ('Mattle', 'Ruedi', '', None, None, 'GLP', '06', e_1)
        ],
        'election': model,
        'election_compound': model,
        'embed': False,
        'entities': 'Rheintal, Rorschach',
        'groups': [
            ('SVP', 4128, 35),
            ('CVP', 3487, 27),
            ('FDP', 2894, 22),
            ('SP', 2481, 6),
            ('GRÜ', 1424, 9),
            ('GLP', 1165, 6),
            ('EVP', 369, 2)
        ],
        'layout': layout,
        'model': model,
        'request': request,
        'seat_allocations': [
            ['CVP', 27],
            ['EVP', 2],
            ['FDP', 22],
            ['GLP', 6],
            ['GRÜ', 9],
            ['SP', 6],
            ['SVP', 35]
        ],
        'superregions': {},
        'party_years': ['2020'],
        'party_deltas': False,
        'party_results': {
            '2020': [
                ['CVP', 27, Decimal('3487.00'), '21.86%'],
                ['EVP', 2, Decimal('369.00'), '2.31%'],
                ['FDP', 22, Decimal('2894.00'), '18.15%'],
                ['GLP', 6, Decimal('1165.00'), '7.30%'],
                ['GRÜ', 9, Decimal('1424.00'), '8.93%'],
                ['SP', 6, Decimal('2481.00'), '15.56%'],
                ['SVP', 35, Decimal('4128.00'), '25.88%']
            ]
        },
    }

    assert '>Compound</span>' in result
    assert '2 of 2' in result
    assert f'<div>{e_1}, {e_2}</div>'
    assert 'election-compound-candidates-table' in result
    assert 'Bruss-Schmidheiny Carmen' in result
    assert 'election-compound-districts-table' in result
    assert '10 of 10' in result
    assert '9 of 9' in result
    assert '17 of 17' in result
    assert '13 of 13' in result
    assert 'data-text="3487.00"' in result
    assert 'data-dataurl="ElectionCompound/list-groups-data"' in result
    assert '2' in result
    assert '2' in result
    assert '02.01.2022' in result
    assert 'election-compound-superregions-table' in result
    assert 'ElectionCompound/by-district' in result
    assert 'ElectionCompound/by-superregion' in result
    assert 'is-completed' in result
    assert 'is-not-completed' not in result
    assert (
        'data-dataurl="ElectionCompound/party-strengths-data?horizontal=True"'
    ) in result
    assert (
        'data-dataurl="ElectionCompound/party-strengths-data?horizontal=False"'
    ) in result
    assert "panel_2020" in result
    assert ">2.31%<" in result
    assert 'class-for-title' in result
    assert 'class-for-progress' in result
    assert 'class-for-counted-entities' in result
    assert 'class-for-candidates-table' in result
    assert 'class-for-districts-table' in result
    assert 'class-for-districts-map' in result
    assert 'class-for-list-groups-table' in result
    assert 'class-for-list-groups-chart' in result
    assert 'class-for-number-of-counted-entities' in result
    assert 'class-for-total-entities' in result
    assert 'class-for-last-result-change' in result
    assert 'class-for-seat-allocation-table' in result
    assert 'class-for-seat-allocation-chart' in result
    assert 'class-for-superregions-table' in result
    assert 'class-for-superregions-map' in result
    assert 'class-for-party-strengths-chart-1' in result
    assert 'class-for-party-strengths-chart-2' in result
    assert 'class-for-party-strengths-table-1' in result
    assert 'class-for-party-strengths-table-2' in result
