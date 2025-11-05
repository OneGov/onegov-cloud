from __future__ import annotations

from datetime import date
from decimal import Decimal
from freezegun import freeze_time
from lxml import etree
from onegov.core.templates import PageTemplate
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.models import ProporzElection
from onegov.election_day.screen_widgets import (
    AbsoluteMajorityWidget,
    AllocatedMandatesWidget,
    CountedEntitiesWidget,
    ElectionCandidatesByEntityTableWidget,
    ElectionCandidatesChartWidget,
    ElectionCandidatesTableWidget,
    ElectionListsChartWidget,
    ElectionListsTableWidget,
    ElectionPartyStrengthsChartWidget,
    ElectionPartyStrengthsTableWidget,
    ElectionTurnoutWidget,
    IfAbsoluteMajorityWidget,
    IfCompletedWidget,
    IfNotCompletedWidget,
    IfRelateMajorityWidget,
    LastResultChangeWidget,
    MandatesWidget,
    ModelProgressWidget,
    ModelTitleWidget,
    NumberOfCountedEntitiesWidget,
    NumberOfMandatesWidget,
    TotalEntitiesWidget,
)
from tests.onegov.election_day.common import DummyRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.widgets import Widget
    from ..conftest import ImportTestDatasets, TestApp


def test_majorz_election_widgets(
    election_day_app_zg: TestApp,
    import_test_datasets: ImportTestDatasets
) -> None:

    structure = """
        <model-title class="my-class-1"/>
        <model-progress class="my-class-2"/>
        <counted-entities class="my-class-3"/>
        <election-candidates-table class="my-class-4" lists="SP, Grüne,"/>
        <election-candidates-chart class="my-class-5"/>
        <election-candidates-chart class="my-class-6" limit="2"
            lists="x,y" sort-by-lists="True" elected="True"/>
        <election-candidates-by-entity-table class="my-class-7"/>
        <number-of-counted-entities class="my-class-8"/>
        <total-entities class="my-class-9"/>
        <election-turnout class="my-class-a"/>
        <absolute-majority class="my-class-b"/>
        <allocated-mandates class="my-class-c"/>
        <number-of-mandates class="my-class-d"/>
        <mandates class="my-class-e"/>
        <last-result-change class="my-class-f"/>
        <if-completed>is-completed</if-completed>
        <if-not-completed>is-not-completed</if-not-completed>
        <if-absolute-majority>is-am</if-absolute-majority>
        <if-relative-majority>is-rm</if-relative-majority>
    """
    widgets: list[Widget] = [
        AbsoluteMajorityWidget(),
        AllocatedMandatesWidget(),
        CountedEntitiesWidget(),
        ElectionCandidatesByEntityTableWidget(),
        ElectionCandidatesChartWidget(),
        ElectionCandidatesTableWidget(),
        ElectionTurnoutWidget(),
        IfAbsoluteMajorityWidget(),
        IfCompletedWidget(),
        IfNotCompletedWidget(),
        IfRelateMajorityWidget(),
        LastResultChangeWidget(),
        MandatesWidget(),
        ModelProgressWidget(),
        ModelTitleWidget(),
        NumberOfCountedEntitiesWidget(),
        NumberOfMandatesWidget(),
        TotalEntitiesWidget(),
    ]

    # Empty
    session = election_day_app_zg.session()
    session.add(
        Election(title='Election', domain='canton', date=date(2015, 6, 18))
    )
    session.flush()
    model = session.query(Election).one()
    request: Any = DummyRequest(app=election_day_app_zg, session=session)
    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [],
        'candidates_by_entites': ([], []),
        'election': model,
        'embed': False,
        'entities': '',
        'layout': layout,
        'model': model,
        'request': request,
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Election</span>' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert 'is-am' not in result
    assert 'is-rm' not in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result

    # Add intermediate results
    with freeze_time('2022-01-01 12:00'):
        results = import_test_datasets(
            'internal',
            'election',
            'zg',
            'canton',
            'majorz',
            date_=date(2015, 10, 18),
            number_of_mandates=2,
            dataset_name='staenderatswahl-2015-intermediate',
            app_session=session
        )
        assert len(results) == 1
        model, errors = next(iter(results.values()))
        model.majority_type = 'absolute'
        assert not errors
        session.add(model)
        session.flush()

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data['candidates'] == [
        (10693, 'Hegglin', 'Peter', True, 'CVP', Decimal('63.3'), None, None),
        (10103, 'Eder', 'Joachim', True, 'FDP', Decimal('59.8'), None, None),
        (4845, 'Brandenberg', 'Manuel', False, 'SVP', Decimal('28.7'), None,
         None),
        (2890, 'Gysel', 'Barbara', False, 'SP', Decimal('17.1'), None, None),
        (2541, 'Lustenberger', 'Andreas', False, 'Grüne', Decimal('15.0'),
         None, None),
        (746, 'Thöni', 'Stefan', False, 'Piraten', Decimal('4.4'), None, None)
    ]

    assert [c[1:] for c in data['candidates_by_entites'][0]] == [
        ('Hegglin', 'Peter', 10693),
        ('Eder', 'Joachim', 10103),
        ('Brandenberg', 'Manuel', 4845),
        ('Gysel', 'Barbara', 2890),
        ('Lustenberger', 'Andreas', 2541),
        ('Thöni', 'Stefan', 746)
    ]
    assert data['candidates_by_entites'][1] == [
        ('Baar', [
            ('Baar', 'Hegglin', 'Peter', 4207),
            ('Baar', 'Eder', 'Joachim', 4237),
            ('Baar', 'Brandenberg', 'Manuel', 2100),
            ('Baar', 'Gysel', 'Barbara', 1264),
            ('Baar', 'Lustenberger', 'Andreas', 1269),
            ('Baar', 'Thöni', 'Stefan', 320)
        ]),
        ('Cham', [
            ('Cham', 'Hegglin', 'Peter', 2905),
            ('Cham', 'Eder', 'Joachim', 2726),
            ('Cham', 'Brandenberg', 'Manuel', 1404),
            ('Cham', 'Gysel', 'Barbara', 888),
            ('Cham', 'Lustenberger', 'Andreas', 685),
            ('Cham', 'Thöni', 'Stefan', 232)
        ]),
        ('Hünenberg', [
            ('Hünenberg', 'Hegglin', 'Peter', 2205),
            ('Hünenberg', 'Eder', 'Joachim', 2098),
            ('Hünenberg', 'Brandenberg', 'Manuel', 881),
            ('Hünenberg', 'Gysel', 'Barbara', 540),
            ('Hünenberg', 'Lustenberger', 'Andreas', 397),
            ('Hünenberg', 'Thöni', 'Stefan', 140)
        ]),
        ('Menzingen', [
            ('Menzingen', 'Hegglin', 'Peter', 1376),
            ('Menzingen', 'Eder', 'Joachim', 1042),
            ('Menzingen', 'Brandenberg', 'Manuel', 460),
            ('Menzingen', 'Gysel', 'Barbara', 198),
            ('Menzingen', 'Lustenberger', 'Andreas', 190),
            ('Menzingen', 'Thöni', 'Stefan', 54)
        ])
    ]
    assert data['election'] == model
    assert data['embed'] == False
    assert data['entities'] == 'Baar, Cham, Hünenberg, Menzingen'
    assert data['layout'] == layout
    assert data['model'] == model
    assert data['request'] == request

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert 'is-am' in result
    assert 'is-rm' not in result
    assert 'majorz_internal_staenderatswahl-2015-intermediate' in result
    assert '4 of 11' in result
    assert 'Baar, Cham, Hünenberg, Menzingen' in result
    assert 'election-candidates-table' in result
    assert 'data-text="10693"' not in result
    assert 'data-text="2890"' in result
    assert 'data-text="2541"' in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=0&amp;lists=&amp;elected=&amp;sort_by_lists=&amp;entity="'
    ) in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True'
        '&amp;sort_by_lists=True&amp;entity="'
    ) in result
    assert 'election-candidates-by-entity-table' in result
    assert '4' in result
    assert '11' in result
    assert '52.32 %' in result
    assert '18.191' in result
    assert '0' in result
    assert '2' in result
    assert '0 of 2' in result
    assert '01.01.2022' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result

    # Add final results
    with freeze_time('2022-01-02 12:00'):
        results = import_test_datasets(
            'internal',
            'election',
            'zg',
            'canton',
            'majorz',
            date_=date(2015, 10, 18),
            number_of_mandates=2,
            dataset_name='staenderatswahl-2015',
            app_session=session
        )
        assert len(results) == 1
        model, errors = next(iter(results.values()))
        assert not errors
        model.majority_type = 'relative'
        session.add(model)
        session.flush()

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data['candidates'] == [
        (24132, 'Hegglin', 'Peter', True, 'CVP', Decimal('62.3'), None, None),
        (23620, 'Eder', 'Joachim', True, 'FDP', Decimal('61.0'), None, None),
        (10997, 'Brandenberg', 'Manuel', False, 'SVP', Decimal('28.4'), None,
         None),
        (6612, 'Gysel', 'Barbara', False, 'SP', Decimal('17.1'), None, None),
        (5691, 'Lustenberger', 'Andreas', False, 'Grüne', Decimal('14.7'),
         None, None),
        (1709, 'Thöni', 'Stefan', False, 'Piraten', Decimal('4.4'), None, None)
    ]
    assert [c[1:] for c in data['candidates_by_entites'][0]] == [
        ('Hegglin', 'Peter', 24132),
        ('Eder', 'Joachim', 23620),
        ('Brandenberg', 'Manuel', 10997),
        ('Gysel', 'Barbara', 6612),
        ('Lustenberger', 'Andreas', 5691),
        ('Thöni', 'Stefan', 1709)
    ]
    assert data['candidates_by_entites'][1] == [
        ('Baar', [
            ('Baar', 'Hegglin', 'Peter', 4207),
            ('Baar', 'Eder', 'Joachim', 4237),
            ('Baar', 'Brandenberg', 'Manuel', 2100),
            ('Baar', 'Gysel', 'Barbara', 1264),
            ('Baar', 'Lustenberger', 'Andreas', 1269),
            ('Baar', 'Thöni', 'Stefan', 320)
        ]),
        ('Cham', [
            ('Cham', 'Hegglin', 'Peter', 2905),
            ('Cham', 'Eder', 'Joachim', 2726),
            ('Cham', 'Brandenberg', 'Manuel', 1404),
            ('Cham', 'Gysel', 'Barbara', 888),
            ('Cham', 'Lustenberger', 'Andreas', 685),
            ('Cham', 'Thöni', 'Stefan', 232)
        ]),
        ('Hünenberg', [
            ('Hünenberg', 'Hegglin', 'Peter', 2205),
            ('Hünenberg', 'Eder', 'Joachim', 2098),
            ('Hünenberg', 'Brandenberg', 'Manuel', 881),
            ('Hünenberg', 'Gysel', 'Barbara', 540),
            ('Hünenberg', 'Lustenberger', 'Andreas', 397),
            ('Hünenberg', 'Thöni', 'Stefan', 140)
        ]),
        ('Menzingen', [
            ('Menzingen', 'Hegglin', 'Peter', 1376),
            ('Menzingen', 'Eder', 'Joachim', 1042),
            ('Menzingen', 'Brandenberg', 'Manuel', 460),
            ('Menzingen', 'Gysel', 'Barbara', 198),
            ('Menzingen', 'Lustenberger', 'Andreas', 190),
            ('Menzingen', 'Thöni', 'Stefan', 54)
        ]),
        ('Neuheim', [
            ('Neuheim', 'Hegglin', 'Peter', 511),
            ('Neuheim', 'Eder', 'Joachim', 453),
            ('Neuheim', 'Brandenberg', 'Manuel', 235),
            ('Neuheim', 'Gysel', 'Barbara', 92),
            ('Neuheim', 'Lustenberger', 'Andreas', 94),
            ('Neuheim', 'Thöni', 'Stefan', 26)
        ]),
        ('Oberägeri', [
            ('Oberägeri', 'Hegglin', 'Peter', 1276),
            ('Oberägeri', 'Eder', 'Joachim', 1380),
            ('Oberägeri', 'Brandenberg', 'Manuel', 656),
            ('Oberägeri', 'Gysel', 'Barbara', 191),
            ('Oberägeri', 'Lustenberger', 'Andreas', 150),
            ('Oberägeri', 'Thöni', 'Stefan', 72)
        ]),
        ('Risch', [
            ('Risch', 'Hegglin', 'Peter', 1730),
            ('Risch', 'Eder', 'Joachim', 1797),
            ('Risch', 'Brandenberg', 'Manuel', 1041),
            ('Risch', 'Gysel', 'Barbara', 391),
            ('Risch', 'Lustenberger', 'Andreas', 362),
            ('Risch', 'Thöni', 'Stefan', 137)
        ]),
        ('Steinhausen', [
            ('Steinhausen', 'Hegglin', 'Peter', 1883),
            ('Steinhausen', 'Eder', 'Joachim', 1827),
            ('Steinhausen', 'Brandenberg', 'Manuel', 789),
            ('Steinhausen', 'Gysel', 'Barbara', 523),
            ('Steinhausen', 'Lustenberger', 'Andreas', 490),
            ('Steinhausen', 'Thöni', 'Stefan', 171)
        ]),
        ('Unterägeri', [
            ('Unterägeri', 'Hegglin', 'Peter', 1779),
            ('Unterägeri', 'Eder', 'Joachim', 2054),
            ('Unterägeri', 'Brandenberg', 'Manuel', 860),
            ('Unterägeri', 'Gysel', 'Barbara', 320),
            ('Unterägeri', 'Lustenberger', 'Andreas', 258),
            ('Unterägeri', 'Thöni', 'Stefan', 85)
        ]),
        ('Walchwil', [
            ('Walchwil', 'Hegglin', 'Peter', 801),
            ('Walchwil', 'Eder', 'Joachim', 756),
            ('Walchwil', 'Brandenberg', 'Manuel', 416),
            ('Walchwil', 'Gysel', 'Barbara', 151),
            ('Walchwil', 'Lustenberger', 'Andreas', 93),
            ('Walchwil', 'Thöni', 'Stefan', 39)
        ]),
        ('Zug', [
            ('Zug', 'Hegglin', 'Peter', 5459),
            ('Zug', 'Eder', 'Joachim', 5250),
            ('Zug', 'Brandenberg', 'Manuel', 2155),
            ('Zug', 'Gysel', 'Barbara', 2054),
            ('Zug', 'Lustenberger', 'Andreas', 1703),
            ('Zug', 'Thöni', 'Stefan', 433)
        ])
    ]

    assert data['election'] == model
    assert data['embed'] == False
    assert data['entities'] == (
        'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
        'Steinhausen, Unterägeri, Walchwil, Zug'
    )
    assert data['layout'] == layout
    assert data['model'] == model
    assert data['request'] == request

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert 'is-am' not in result
    assert 'is-rm' in result
    assert 'majorz_internal_staenderatswahl-2015' in result
    assert '11 of 11' in result
    assert (
        'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
        'Steinhausen, Unterägeri, Walchwil, Zug'
    ) in result
    assert 'election-candidates-table' in result
    assert 'data-text="24132"' not in result
    assert 'data-text="6612"' in result
    assert 'data-text="5691"' in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=0&amp;lists=&amp;elected=&amp;sort_by_lists=&amp;entity="'
    ) in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True'
        '&amp;sort_by_lists=True&amp;entity="'
    ) in result
    assert 'election-candidates-by-entity-table' in result
    assert '11' in result
    assert '11' in result
    assert '53.01 %' in result
    assert '18.191' in result
    assert '2' in result
    assert '2' in result
    assert '2 of 2' in result
    assert 'is-completed' in result
    assert 'is-not-completed' not in result
    assert '02.01.2022' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result


def test_proporz_election_widgets(
    election_day_app_zg: TestApp,
    import_test_datasets: ImportTestDatasets
) -> None:

    structure = """
        <model-title class="my-class-1"/>
        <model-progress class="my-class-2"/>
        <counted-entities class="my-class-3"/>
        <election-candidates-table class="my-class-4"
            lists="SP Migrant.,,,,SVP Int."/>
        <election-candidates-chart class="my-class-5"/>
        <election-candidates-chart class="my-class-6" limit="2"
            lists="x,y" sort-by-lists="True" elected="True"/>
        <election-lists-table class="my-class-7"
            names="SP Männer, SP Frauen,   ALG Junge    "/>
        <election-lists-chart class="my-class-8"/>
        <election-lists-chart class="my-class-9" limit="3"
            names="a,b" sort-by-names="True"/>
        <number-of-counted-entities class="my-class-a"/>
        <total-entities class="my-class-b"/>
        <election-turnout class="my-class-c"/>
        <allocated-mandates class="my-class-d"/>
        <number-of-mandates class="my-class-e"/>
        <mandates class="my-class-f"/>
        <last-result-change class="my-class-g"/>
        <if-completed>is-completed</if-completed>
        <if-not-completed>is-not-completed</if-not-completed>
        <election-party-strengths-chart class="my-class-h" horizontal="true"/>
        <election-party-strengths-chart class="my-class-i" horizontal="false"/>
        <election-party-strengths-table class="my-class-j"/>
        <election-party-strengths-table class="my-class-k" year="2019"/>
    """
    widgets: list[Widget] = [
        AllocatedMandatesWidget(),
        CountedEntitiesWidget(),
        ElectionCandidatesChartWidget(),
        ElectionCandidatesTableWidget(),
        ElectionListsChartWidget(),
        ElectionListsTableWidget(),
        ElectionPartyStrengthsChartWidget(),
        ElectionPartyStrengthsTableWidget(),
        ElectionTurnoutWidget(),
        IfCompletedWidget(),
        IfNotCompletedWidget(),
        LastResultChangeWidget(),
        MandatesWidget(),
        ModelProgressWidget(),
        ModelTitleWidget(),
        NumberOfCountedEntitiesWidget(),
        NumberOfMandatesWidget(),
        TotalEntitiesWidget(),
    ]

    # Empty
    session = election_day_app_zg.session()
    session.add(
        ProporzElection(
            title='Election', domain='canton', date=date(2015, 6, 18)
        )
    )
    model = session.query(ProporzElection).one()
    request: Any = DummyRequest(app=election_day_app_zg, session=session)
    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [],
        'election': model,
        'embed': False,
        'entities': '',
        'layout': layout,
        'lists': [],
        'model': model,
        'party_deltas': False,
        'party_results': {},
        'party_years': [],
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Election</span>' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result
    assert 'my-class-g' in result
    assert 'my-class-h' in result
    assert 'my-class-i' in result
    assert 'my-class-j' in result
    assert 'my-class-k' in result

    # Add intermediate results
    with freeze_time('2022-01-01 12:00'):
        results = import_test_datasets(
            'internal',
            'election',
            'zg',
            'canton',
            'proporz',
            date_=date(2015, 10, 18),
            number_of_mandates=1,
            dataset_name='nationalratswahlen-2015-intermediate',
            app_session=session
        )
        assert len(results) == 1
        model, errors = next(iter(results.values()))
        assert not errors
        session.add(model)
        session.flush()

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [
            (1514, 'Lustenberger', 'Andreas', False, '', 0, 'ALG', '1'),
            (491, 'Estermann', 'Astrid', False, '', 0, 'ALG', '1'),
            (423, 'Schriber-Neiger', 'Hanni', False, '', 0, 'ALG', '1'),
            (1918, 'Schuler', 'Hubert', False, '', 0, 'SP', '10'),
            (1202, 'Bürgi Dellsperger', 'Christina', False, '', 0, 'SP', '10'),
            (691, 'Sivaganesan', 'Rupan', False, '', 0, 'SP', '10'),
            (412, 'Hutter Elsener', 'Simone', False, '', 0, 'SP Frauen', '11'),
            (340, 'Hug', 'Malaika', False, '', 0, 'SP Frauen', '11'),
            (237, 'Mäder Beglinger', 'Anne', False, '', 0, 'SP Frauen', '11'),
            (258, 'Krasnici', 'Denis', False, '', 0, 'SP Juso', '12'),
            (202, 'Spescha', 'Anna', False, '', 0, 'SP Juso', '12'),
            (102, 'Koepfli', 'Virginia', False, '', 0, 'SP Juso', '12'),
            (1355, 'Dzaferi', 'Zari', False, '', 0, 'SP Männer', '13'),
            (218, 'Freimann', 'Fabian', False, '', 0, 'SP Männer', '13'),
            (188, 'Suter', 'Guido', False, '', 0, 'SP Männer', '13'),
            (54, 'Sönmez', 'Sehriban', False, '', 0, 'SP Migrant.', '14'),
            (50, 'Coralic', 'Fadila', False, '', 0, 'SP Migrant.', '14'),
            (38, 'Simsek', 'Deniz', False, '', 0, 'SP Migrant.', '14'),
            (7731, 'Aeschi', 'Thomas', True, '', 0, 'SVP', '15'),
            (2914, 'Werner', 'Thomas', False, '', 0, 'SVP', '15'),
            (2571, 'Villiger', 'Thomas', False, '', 0, 'SVP', '15'),
            (105, 'Pfisterer', 'Luc', False, '', 0, 'SVP Int.', '16'),
            (69, 'Bucher', 'Rinaldo', False, '', 0, 'SVP Int.', '16'),
            (46, 'Hornickel', 'Alexander', False, '', 0, 'SVP Int.', '16'),
            (1153, 'Risi', 'Adrian', False, '', 0, 'SVP WuG', '17'),
            (471, 'Brunner', 'Philip C.', False, '', 0, 'SVP WuG', '17'),
            (268, 'Gertsch', 'Beat', False, '', 0, 'SVP WuG', '17'),
            (101, 'Widmer', 'Fabienne', False, '', 0, 'ALG Junge', '2'),
            (74, 'Gut', 'Christina', False, '', 0, 'ALG Junge', '2'),
            (66, 'Perucchi', 'Alessandro', False, '', 0, 'ALG Junge', '2'),
            (301, 'Haas', 'Esther', False, '', 0, 'ALG Bildung', '3'),
            (221, 'Odermatt', 'Anastas', False, '', 0, 'ALG Bildung', '3'),
            (207, 'Zimmermann Gibson', 'Tabea', False, '', 0, 'ALG Bildung',
             '3'),
            (6719, 'Pfister', 'Gerhard', True, '', 0, 'CVP', '4'),
            (1996, 'Barmet-Schelbert', 'Monika', False, '', 0, 'CVP', '4'),
            (1340, 'Hausheer', 'Andreas', False, '', 0, 'CVP', '4'),
            (2407, 'Bieri', 'Anna', False, '', 0, 'CVP Junge', '5'),
            (587, 'Iten', 'Christoph', False, '', 0, 'CVP Junge', '5'),
            (525, 'Kremmel', 'Corina', False, '', 0, 'CVP Junge', '5'),
            (4309, 'Pezzatti', 'Bruno', True, '', 0, 'FDP Ost', '6'),
            (1083, 'Ingold', 'Gabriela', False, '', 0, 'FDP Ost', '6'),
            (705, 'Mollet', 'Patrick', False, '', 0, 'FDP Ost', '6'),
            (897, 'Grüter', 'Arno', False, '', 0, 'FDP West', '7'),
            (717, 'Gygli', 'Daniel', False, '', 0, 'FDP West', '7'),
            (493, 'Siegrist', 'Birgitt', False, '', 0, 'FDP West', '7'),
            (731, 'Stadlin', 'Daniel', False, '', 0, 'glp', '8'),
            (508, 'Kottelat Schloesing', 'Michèle', False, '', 0, 'glp', '8'),
            (451, 'Soltermann', 'Claus', False, '', 0, 'glp', '8'),
            (260, 'Mauchle', 'Florian', False, '', 0, 'Piraten', '9'),
            (211, 'Thöni', 'Stefan', False, '', 0, 'Piraten', '9')
        ],
        'election': model,
        'embed': False,
        'entities': 'Baar, Cham, Hünenberg, Menzingen',
        'layout': layout,
        'lists': [
            (13532, 'SVP', 1),
            (10247, 'CVP', 1),
            (6219, 'FDP Ost', 1),
            (3866, 'SP', 0),
            (3549, 'CVP Junge', 0),
            (2459, 'ALG', 0),
            (2143, 'FDP West', 0),
            (1933, 'SVP WuG', 0),
            (1814, 'SP Männer', 0),
            (1718, 'glp', 0),
            (998, 'SP Frauen', 0),
            (735, 'ALG Bildung', 0),
            (567, 'SP Juso', 0),
            (475, 'Piraten', 0),
            (245, 'ALG Junge', 0),
            (223, 'SVP Int.', 0),
            (146, 'SP Migrant.', 0)
        ],
        'model': model,
        'party_deltas': False,
        'party_results': {},
        'party_years': [],
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert 'proporz_internal_nationalratswahlen-2015-intermediate' in result
    assert '4 of 11' in result
    assert 'Baar, Cham, Hünenberg, Menzingen' in result
    assert 'election-candidates-table' in result
    assert 'data-text="1514"' not in result
    assert 'data-text="54"' in result
    assert 'data-text="50"' in result
    assert 'data-text="105"' in result
    assert 'data-text="69"' in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=0&amp;lists=&amp;elected=&amp;sort_by_lists=&amp;entity="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True'
        '&amp;sort_by_lists=True&amp;entity="'
    ) in result
    assert 'election-lists-table' in result
    assert 'data-text="13532"' not in result
    assert 'data-text="1814"' in result
    assert 'data-text="998"' in result
    assert 'data-text="245"' in result
    assert (
        'data-dataurl="ProporzElection/lists-data'
        '?limit=0&amp;names=&amp;sort_by_names=&amp;entity="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/lists-data'
        '?limit=03&amp;names=a,b&amp;sort_by_names=True&amp;entity="'
    ) in result
    assert '4' in result
    assert '11' in result
    assert '53.27 %' in result
    assert '0' in result
    assert '1' in result
    assert '0 of 1' in result
    assert '01.01.2022' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert (
        'data-dataurl="ProporzElection/party-strengths-data?horizontal=True"'
    ) in result
    assert (
        'data-dataurl="ProporzElection/party-strengths-data?horizontal=False"'
    ) in result
    assert 'tab-navigation' not in result
    assert 'tabs-content' not in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result
    assert 'my-class-g' in result
    assert 'my-class-h' in result
    assert 'my-class-i' in result
    assert 'my-class-j' in result
    assert 'my-class-k' in result

    # Add final results
    with freeze_time('2022-01-02 12:00'):
        results = import_test_datasets(
            'internal',
            'election',
            'zg',
            'canton',
            'proporz',
            date_=date(2015, 10, 18),
            number_of_mandates=1,
            dataset_name='nationalratswahlen-2015',
            app_session=session
        )
        assert len(results) == 1
        model, errors = next(iter(results.values()))
        assert not errors
        session.add(model)
        session.flush()
        results_ = import_test_datasets(
            'internal',
            'parties',
            'zg',
            'canton',
            election=model,
            dataset_name='nationalratswahlen-2015-parteien',
        )
        assert len(results) == 1
        errors_ = next(iter(results_.values()))
        assert not errors_

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [
            (3240, 'Lustenberger', 'Andreas', False, '', 0, 'ALG', '1'),
            (1327, 'Estermann', 'Astrid', False, '', 0, 'ALG', '1'),
            (1206, 'Schriber-Neiger', 'Hanni', False, '', 0, 'ALG', '1'),
            (3859, 'Schuler', 'Hubert', False, '', 0, 'SP', '10'),
            (2987, 'Bürgi Dellsperger', 'Christina', False, '', 0, 'SP', '10'),
            (1874, 'Sivaganesan', 'Rupan', False, '', 0, 'SP', '10'),
            (929, 'Hutter Elsener', 'Simone', False, '', 0, 'SP Frauen', '11'),
            (684, 'Hug', 'Malaika', False, '', 0, 'SP Frauen', '11'),
            (561, 'Mäder Beglinger', 'Anne', False, '', 0, 'SP Frauen', '11'),
            (555, 'Spescha', 'Anna', False, '', 0, 'SP Juso', '12'),
            (550, 'Krasnici', 'Denis', False, '', 0, 'SP Juso', '12'),
            (218, 'Koepfli', 'Virginia', False, '', 0, 'SP Juso', '12'),
            (2303, 'Dzaferi', 'Zari', False, '', 0, 'SP Männer', '13'),
            (545, 'Suter', 'Guido', False, '', 0, 'SP Männer', '13'),
            (394, 'Freimann', 'Fabian', False, '', 0, 'SP Männer', '13'),
            (144, 'Coralic', 'Fadila', False, '', 0, 'SP Migrant.', '14'),
            (117, 'Sönmez', 'Sehriban', False, '', 0, 'SP Migrant.', '14'),
            (82, 'Simsek', 'Deniz', False, '', 0, 'SP Migrant.', '14'),
            (17034, 'Aeschi', 'Thomas', True, '', 0, 'SVP', '15'),
            (7206, 'Werner', 'Thomas', False, '', 0, 'SVP', '15'),
            (5629, 'Villiger', 'Thomas', False, '', 0, 'SVP', '15'),
            (269, 'Pfisterer', 'Luc', False, '', 0, 'SVP Int.', '16'),
            (168, 'Bucher', 'Rinaldo', False, '', 0, 'SVP Int.', '16'),
            (132, 'Hornickel', 'Alexander', False, '', 0, 'SVP Int.', '16'),
            (2607, 'Risi', 'Adrian', False, '', 0, 'SVP WuG', '17'),
            (1159, 'Brunner', 'Philip C.', False, '', 0, 'SVP WuG', '17'),
            (607, 'Gertsch', 'Beat', False, '', 0, 'SVP WuG', '17'),
            (345, 'Widmer', 'Fabienne', False, '', 0, 'ALG Junge', '2'),
            (235, 'Gut', 'Christina', False, '', 0, 'ALG Junge', '2'),
            (222, 'Perucchi', 'Alessandro', False, '', 0, 'ALG Junge', '2'),
            (637, 'Odermatt', 'Anastas', False, '', 0, 'ALG Bildung', '3'),
            (559, 'Haas', 'Esther', False, '', 0, 'ALG Bildung', '3'),
            (490, 'Zimmermann Gibson', 'Tabea', False, '', 0, 'ALG Bildung',
             '3'),
            (16134, 'Pfister', 'Gerhard', True, '', 0, 'CVP', '4'),
            (4093, 'Barmet-Schelbert', 'Monika', False, '', 0, 'CVP', '4'),
            (3606, 'Hausheer', 'Andreas', False, '', 0, 'CVP', '4'),
            (3908, 'Bieri', 'Anna', False, '', 0, 'CVP Junge', '5'),
            (1394, 'Iten', 'Christoph', False, '', 0, 'CVP Junge', '5'),
            (1163, 'Kremmel', 'Corina', False, '', 0, 'CVP Junge', '5'),
            (10174, 'Pezzatti', 'Bruno', True, '', 0, 'FDP Ost', '6'),
            (3637, 'Ingold', 'Gabriela', False, '', 0, 'FDP Ost', '6'),
            (2190, 'Mollet', 'Patrick', False, '', 0, 'FDP Ost', '6'),
            (1706, 'Grüter', 'Arno', False, '', 0, 'FDP West', '7'),
            (1378, 'Gygli', 'Daniel', False, '', 0, 'FDP West', '7'),
            (1142, 'Siegrist', 'Birgitt', False, '', 0, 'FDP West', '7'),
            (1823, 'Stadlin', 'Daniel', False, '', 0, 'glp', '8'),
            (1256, 'Kottelat Schloesing', 'Michèle', False, '', 0, 'glp', '8'),
            (1043, 'Soltermann', 'Claus', False, '', 0, 'glp', '8'),
            (629, 'Mauchle', 'Florian', False, '', 0, 'Piraten', '9'),
            (488, 'Thöni', 'Stefan', False, '', 0, 'Piraten', '9')
        ],
        'election': model,
        'embed': False,
        'entities': (
            'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
            'Steinhausen, Unterägeri, Walchwil, Zug'
        ),
        'layout': layout,
        'lists': [
            (30532, 'SVP', 1),
            (24335, 'CVP', 1),
            (16285, 'FDP Ost', 1),
            (8868, 'SP', 0),
            (6521, 'CVP Junge', 0),
            (5844, 'ALG', 0),
            (4436, 'SVP WuG', 0),
            (4299, 'FDP West', 0),
            (4178, 'glp', 0),
            (3314, 'SP Männer', 0),
            (2186, 'SP Frauen', 0),
            (1701, 'ALG Bildung', 0),
            (1333, 'SP Juso', 0),
            (1128, 'Piraten', 0),
            (807, 'ALG Junge', 0),
            (575, 'SVP Int.', 0),
            (347, 'SP Migrant.', 0)
        ],
        'model': model,
        'party_deltas': True,
        'party_results': {
            '2011': [
                ['AL', 0, 17972, '15.4%', ''],
                ['CVP', 1, 28413, '24.3%', ''],
                ['FDP', 1, 22494, '19.2%', ''],
                ['GLP', 0, 7943, '6.8%', ''],
                ['SP', 0, 6167, '5.3%', ''],
                ['SVP', 1, 33116, '28.3%', '']
            ],
            '2015': [
                ['AL', 0, 8352, '7.2%', '-8.2%'],
                ['CVP', 1, 30856, '26.4%', '2.1%'],
                ['FDP', 1, 20584, '17.6%', '-1.6%'],
                ['GLP', 0, 4178, '3.6%', '-3.2%'],
                ['SP', 0, 16048, '13.8%', '8.5%'],
                ['SVP', 1, 35543, '30.5%', '2.2%']
            ]
        },
        'party_years': ['2011', '2015'],
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert 'proporz_internal_nationalratswahlen-2015' in result
    assert '11 of 11' in result
    assert (
        'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
        'Steinhausen, Unterägeri, Walchwil, Zug'
    ) in result
    assert 'election-candidates-table' in result
    assert 'data-text="3240"' not in result
    assert 'data-text="144"' in result
    assert 'data-text="117"' in result
    assert 'data-text="269"' in result
    assert 'data-text="168"' in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=0&amp;lists=&amp;elected=&amp;sort_by_lists=&amp;entity="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True'
        '&amp;sort_by_lists=True&amp;entity="'
    ) in result
    assert 'election-lists-table' in result
    assert 'data-text="30532"' not in result
    assert 'data-text="3314"' in result
    assert 'data-text="2186"' in result
    assert 'data-text="807"' in result
    assert (
        'data-dataurl="ProporzElection/lists-data'
        '?limit=0&amp;names=&amp;sort_by_names=&amp;entity="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/lists-data'
        '?limit=03&amp;names=a,b&amp;sort_by_names=True&amp;entity="'
    ) in result
    assert '11' in result
    assert '11' in result
    assert '53.74 %' in result
    assert '3' in result
    assert '1' in result
    assert '3 of 1' in result
    assert '02.01.2022' in result
    assert 'is-completed' in result
    assert 'is-not-completed' not in result
    assert (
        'data-dataurl="ProporzElection/party-strengths-data?horizontal=True"'
    ) in result
    assert (
        'data-dataurl="ProporzElection/party-strengths-data?horizontal=False"'
    ) in result
    assert 'panel_2011' in result
    assert '>15.4%<' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result
    assert 'my-class-g' in result
    assert 'my-class-h' in result
    assert 'my-class-i' in result
    assert 'my-class-j' in result
    assert 'my-class-k' in result
