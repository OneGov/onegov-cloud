from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from lxml import etree
from onegov.core.templates import PageTemplate
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
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


def test_election_compound_part_widgets(
    election_day_app_bl: TestApp,
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
    session = election_day_app_bl.session()
    session.add(
        ElectionCompound(
            title='Compound', domain='canton', date=date(2019, 3, 31),
            completes_manually=True, voters_counts=True,
        )
    )
    compound = session.query(ElectionCompound).one()
    model = ElectionCompoundPart(compound, 'superregion', 'Region 3')
    request: Any = DummyRequest(app=election_day_app_bl, session=session)
    layout = ElectionCompoundPartLayout(model, request)
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

    assert '>Compound Region 3</span>' in result
    assert 'ElectionCompoundPart/by-district' in result
    assert 'ElectionCompoundPart/by-superregion' in result
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

    # Add final results (actually final, but not manually completed)
    with freeze_time('2022-01-01 12:00'):
        session.delete(compound)
        results = import_test_datasets(
            app_session=session,
            api_format='internal',
            model='election_compound',
            principal='bl',
            domain='region',
            domain_segment=(
                'Allschwil',
                'Binningen',
                'Oberwil',
                'Reinach',
                'Münchenstein',
                'Muttenz',
                'Laufen',
                'Pratteln',
                'Liestal',
                'Sissach',
                'Gelterkinden',
                'Waldenburg',
            ),
            domain_supersegment=(
                'Region 1',
                'Region 1',
                'Region 1',
                'Region 2',
                'Region 2',
                'Region 2',
                'Region 2',
                'Region 3',
                'Region 3',
                'Region 4',
                'Region 4',
                'Region 4',
            ),
            number_of_mandates=(
                7,
                7,
                9,
                10,
                7,
                9,
                6,
                8,
                9,
                6,
                6,
                6,
            ),
            date_=date(2019, 3, 31),
            dataset_name='landratswahlen-2019'
        )
        assert len(results) == 1
        compound, errors = next(iter(results.values()))
        assert not errors
        compound.completes_manually = True
        compound.manually_completed = False
        compound.title = 'Compound'
        session.flush()
        model = ElectionCompoundPart(compound, 'superregion', 'Region 3')

    layout = ElectionCompoundPartLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    e_1 = 'proporz_internal_liestal'
    e_2 = 'proporz_internal_pratteln'
    assert data == {
        'districts': {
            e_1: ('Liestal', f'ProporzElection/{e_1}', 'Region 3'),
            e_2: ('Pratteln', f'ProporzElection/{e_2}', 'Region 3'),
        },
        'elected_candidates': [
            ('Burgunder', 'Stephan', 'FDP', 'male', 1975,
             'FDP.Die Liberalen', '01', 'proporz_internal_pratteln'),
            ('Kaufmann-Lang', 'Urs', 'SP', 'undetermined', 1961,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_pratteln'),
            ('Würth', 'Mirjam', 'SP', 'female', 1960,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_pratteln'),
            ('Schneider', 'Urs', 'SVP', 'male', 1974,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_pratteln'),
            ('Trüssel', 'Andi', 'SVP', 'male', 1952,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_pratteln'),
            ('Wolf-Gasser', 'Irene', 'EVP', 'female', 1959,
             'Evangelische Volkspartei', '04', 'proporz_internal_pratteln'),
            ('Ackermann Maurer', 'Stephan', 'Grüne', 'male', 1973,
             'Grüne Baselland', '07', 'proporz_internal_pratteln'),
            ('Steinemann', 'Regula', 'glp', 'female', 1980,
             'Grünliberale Partei Basel-Landschaft', '11',
             'proporz_internal_pratteln'),
            ('Eugster', 'Thomas', 'FDP', 'male', 1970,
             'FDP.Die Liberalen', '01', 'proporz_internal_liestal'),
            ('Lerf', 'Heinz', 'FDP', 'male', 1956,
             'FDP.Die Liberalen', '01', 'proporz_internal_liestal'),
            ('Cucè', 'Tania', 'SP', 'female', 1989,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_liestal'),
            ('Meschberger', 'Pascale', 'SP', 'female', 1974,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_liestal'),
            ('Noack', 'Thomas', 'SP', 'male', 1961,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_liestal'),
            ('Epple', 'Dieter', 'SVP', 'male', 1955,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_liestal'),
            ('Tschudin', 'Reto', 'SVP', 'male', 1984,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_liestal'),
            ('Eichenberger', 'Erika', 'Grüne', 'female', 1963,
             'Grüne Baselland', '07', 'proporz_internal_liestal'),
            ('Franke', 'Meret', 'Grüne', 'female', 1983,
             'Grüne Baselland', '07', 'proporz_internal_liestal')
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

    assert '>Compound Region 3</span>' in result
    assert '0 of 2' in result
    assert f'<div>{e_2}</div>'
    assert 'election-compound-candidates-table' in result
    assert 'Burgunder Stephan' in result
    assert 'election-compound-districts-table' in result
    assert '0 of 8' in result
    assert '7 of 7' in result
    assert '0 of 9' in result
    assert '7 of 7' in result
    assert '01.01.2022' in result
    assert 'election-compound-superregions-table' in result
    assert 'ElectionCompoundPart/by-district' in result
    assert 'ElectionCompoundPart/by-superregion' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert (
        'data-dataurl="ElectionCompoundPart/party-strengths-data'
        '?horizontal=True"'
    ) in result
    assert (
        'data-dataurl="ElectionCompoundPart/party-strengths-data'
        '?horizontal=False"'
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

    # Add final results (actually, set final and add party results)
    with freeze_time('2022-01-02 12:00'):
        results_ = import_test_datasets(
            'internal',
            'parties',
            'bl',
            'region',
            election=model.election_compound,
            dataset_name='landratswahlen-2019-parteien',
        )
        assert len(results) == 1
        errors_ = next(iter(results_.values()))
        assert not errors_
        model.election_compound.manually_completed = True
        session.flush()

    layout = ElectionCompoundPartLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    data['groups'] = [
        (r.name, r.voters_count, r.number_of_mandates) for r in data['groups']
    ]
    e_1 = 'proporz_internal_liestal'
    e_2 = 'proporz_internal_pratteln'
    assert data == {
        'districts': {
            e_1: ('Liestal', f'ProporzElection/{e_1}', 'Region 3'),
            e_2: ('Pratteln', f'ProporzElection/{e_2}', 'Region 3'),
        },
        'elected_candidates': [
            ('Burgunder', 'Stephan', 'FDP', 'male', 1975,
             'FDP.Die Liberalen', '01', 'proporz_internal_pratteln'),
            ('Kaufmann-Lang', 'Urs', 'SP', 'undetermined', 1961,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_pratteln'),
            ('Würth', 'Mirjam', 'SP', 'female', 1960,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_pratteln'),
            ('Schneider', 'Urs', 'SVP', 'male', 1974,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_pratteln'),
            ('Trüssel', 'Andi', 'SVP', 'male', 1952,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_pratteln'),
            ('Wolf-Gasser', 'Irene', 'EVP', 'female', 1959,
             'Evangelische Volkspartei', '04', 'proporz_internal_pratteln'),
            ('Ackermann Maurer', 'Stephan', 'Grüne', 'male', 1973,
             'Grüne Baselland', '07', 'proporz_internal_pratteln'),
            ('Steinemann', 'Regula', 'glp', 'female', 1980,
             'Grünliberale Partei Basel-Landschaft', '11',
             'proporz_internal_pratteln'),
            ('Eugster', 'Thomas', 'FDP', 'male', 1970,
             'FDP.Die Liberalen', '01', 'proporz_internal_liestal'),
            ('Lerf', 'Heinz', 'FDP', 'male', 1956,
             'FDP.Die Liberalen', '01', 'proporz_internal_liestal'),
            ('Cucè', 'Tania', 'SP', 'female', 1989,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_liestal'),
            ('Meschberger', 'Pascale', 'SP', 'female', 1974,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_liestal'),
            ('Noack', 'Thomas', 'SP', 'male', 1961,
             'Sozialdemokratische Partei, JUSO und Gewerkschaften', '02',
             'proporz_internal_liestal'),
            ('Epple', 'Dieter', 'SVP', 'male', 1955,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_liestal'),
            ('Tschudin', 'Reto', 'SVP', 'male', 1984,
             'Schweizerische Volkspartei Baselland', '03',
             'proporz_internal_liestal'),
            ('Eichenberger', 'Erika', 'Grüne', 'female', 1963,
             'Grüne Baselland', '07', 'proporz_internal_liestal'),
            ('Franke', 'Meret', 'Grüne', 'female', 1983,
             'Grüne Baselland', '07', 'proporz_internal_liestal')
        ],
        'election': model,
        'election_compound': model,
        'embed': False,
        'entities': 'Pratteln, Liestal',
        'groups': [],
        'layout': layout,
        'model': model,
        'request': request,
        'seat_allocations': [
            ['SP', 5],
            ['SVP', 4],
            ['BDP', 0],
            ['CVP', 0],
            ['EVP', 1],
            ['FDP', 3],
            ['glp', 1],
            ['Grüne', 3]
        ],
        'superregions': {},
        'party_years': ['2019'],
        'party_deltas': False,
        'party_results': {
            '2019': [
                ['SP', 5, 24972, '24.4%'],
                ['SVP', 4, 24002, '23.4%'],
                ['BDP', 0, 2677, '2.6%'],
                ['CVP', 0, 4399, '4.3%'],
                ['EVP', 1, 5672, '5.5%'],
                ['FDP', 3, 17067, '16.6%'],
                ['glp', 1, 6956, '6.8%'],
                ['Grüne', 3, 16777, '16.4%']
            ]
        },
    }

    assert '>Compound Region 3</span>' in result
    assert '2 of 2' in result
    assert f'<div>{e_1}, {e_2}</div>'
    assert 'election-compound-candidates-table' in result
    assert 'Burgunder Stephan' in result
    assert 'election-compound-districts-table' in result
    assert '8 of 8' in result
    assert '7 of 7' in result
    assert '9 of 9' in result
    assert '7 of 7' in result
    assert 'data-dataurl="ElectionCompoundPart/list-groups-data"' in result
    assert '2' in result
    assert '2' in result
    assert '02.01.2022' in result
    assert 'election-compound-superregions-table' in result
    assert 'ElectionCompoundPart/by-district' in result
    assert 'ElectionCompoundPart/by-superregion' in result
    assert 'is-completed' in result
    assert 'is-not-completed' not in result
    assert (
        'data-dataurl="ElectionCompoundPart/party-strengths-data'
        '?horizontal=True"'
    ) in result
    assert (
        'data-dataurl="ElectionCompoundPart/party-strengths-data'
        '?horizontal=False"'
    ) in result
    assert "panel_2019" in result
    assert ">24.4%<" in result
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
