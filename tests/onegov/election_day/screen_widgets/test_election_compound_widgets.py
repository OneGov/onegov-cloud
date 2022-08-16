from datetime import date
from decimal import Decimal
from freezegun import freeze_time
from lxml import etree
from onegov.ballot import ElectionCompound
from onegov.core.templates import PageTemplate
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.screen_widgets import (
    ColumnWidget,
    CountedEntitiesWidget,
    ElectionCompoundCandidatesTableWidget,
    ElectionCompoundDistrictsTableWidget,
    ElectionCompoundListGroupsChartWidget,
    ElectionCompoundListGroupsTableWidget,
    ElectionCompoundSeatAllocationChartWidget,
    ElectionCompoundSeatAllocationTableWidget,
    LastResultChangeWidget,
    NumberOfCountedEntitiesWidget,
    ProgressWidget,
    RowWidget,
    TitleWidget,
    TotalEntitiesWidget,
)
from tests.onegov.election_day.common import DummyRequest


def test_election_compound_widgets(election_day_app_sg, import_test_datasets):
    structure = """
        <row>
            <column span="1">
                <title class="class-for-title"/>
            </column>
            <column span="1">
                <progress class="class-for-progress"/>
            </column>
            <column span="1">
                <counted-entities class="class-for-counted-entities"/>
            </column>
            <column span="1">
                <election-compound-candidates-table
                 class="class-for-candidates-table"/>
            </column>
            <column span="1">
                <election-compound-districts-table
                 class="class-for-districts-table"/>
            </column>
            <column span="1">
                <election-compound-list-groups-table
                 class="class-for-list-groups-table"/>
            </column>
            <column span="1">
                <election-compound-list-groups-chart
                 class="class-for-list-groups-chart"/>
            </column>
            <column span="1">
                <number-of-counted-entities
                 class="class-for-number-of-counted-entities"/>
            </column>
            <column span="1">
                <total-entities class="class-for-total-entities"/>
            </column>
            <column span="1">
                <last-result-change class="class-for-last-result-change"/>
            </column>
            <column span="1">
                <election-compound-seat-allocation-table
                 class="class-for-seat-allocation-table"/>
            </column>
            <column span="1">
                <election-compound-seat-allocation-chart
                 class="class-for-seat-allocation-chart"/>
            </column>

        </row>
    """
    widgets = [
        RowWidget(),
        ColumnWidget(),
        CountedEntitiesWidget(),
        LastResultChangeWidget(),
        NumberOfCountedEntitiesWidget(),
        ProgressWidget(),
        TitleWidget(),
        TotalEntitiesWidget(),
        ElectionCompoundCandidatesTableWidget(),
        ElectionCompoundDistrictsTableWidget(),
        ElectionCompoundListGroupsChartWidget(),
        ElectionCompoundListGroupsTableWidget(),
        ElectionCompoundSeatAllocationChartWidget(),
        ElectionCompoundSeatAllocationTableWidget(),
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
    request = DummyRequest(app=election_day_app_sg, session=session)
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
        'parties': {},
        'request': request,
        'years': []
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Compound</span>' in result
    assert 'class-for-title' in result
    assert 'class-for-progress' in result
    assert 'class-for-counted-entities' in result
    assert 'class-for-candidates-table' in result
    assert 'class-for-districts-table' in result
    assert 'class-for-list-groups-table' in result
    assert 'class-for-list-groups-chart' in result
    assert 'class-for-number-of-counted-entities' in result
    assert 'class-for-total-entities' in result
    assert 'class-for-last-result-change' in result
    assert 'class-for-seat-allocation-table' in result
    assert 'class-for-seat-allocation-chart' in result

    # Add intermediate results
    with freeze_time('2022-01-01 12:00'):
        election_1, errors = import_test_datasets(
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
        assert not errors
        election_2, errors = import_test_datasets(
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
            e_1: ('Rheintal', f'ProporzElection/{e_1}'),
            e_2: ('Rorschach', f'ProporzElection/{e_2}')
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
        'parties': {},
        'request': request,
        'years': []
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
    assert 'class-for-title' in result
    assert 'class-for-progress' in result
    assert 'class-for-counted-entities' in result
    assert 'class-for-candidates-table' in result
    assert 'class-for-districts-table' in result
    assert 'class-for-list-groups-table' in result
    assert 'class-for-list-groups-chart' in result
    assert 'class-for-number-of-counted-entities' in result
    assert 'class-for-total-entities' in result
    assert 'class-for-last-result-change' in result
    assert 'class-for-seat-allocation-table' in result
    assert 'class-for-seat-allocation-chart' in result

    # Add final results
    with freeze_time('2022-01-02 12:00'):
        election_1, errors = import_test_datasets(
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
        assert not errors
        errors = import_test_datasets(
            'internal',
            'parties',
            'sg',
            'district',
            'proporz',
            election=model,
            dataset_name='kantonsratswahl-2020-parteien',
        )
        assert not errors
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
            e_1: ('Rheintal', f'ProporzElection/{e_1}'),
            e_2: ('Rorschach', f'ProporzElection/{e_2}')
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
        'parties': {
            '0': {
                '2020': {
                    'color': '#0571b0',
                    'mandates': 27,
                    'name': 'CVP',
                    'voters_count': {
                        'permille': Decimal('218.60'),
                        'total': Decimal('3487.00')
                    },
                    'votes': {'permille': 219, 'total': 373080}
                }
            },
            '1': {
                '2020': {
                    'color': '#0571b0',
                    'mandates': 2,
                    'name': 'EVP',
                    'voters_count': {
                        'permille': Decimal('23.10'),
                        'total': Decimal('369.00')
                    },
                    'votes': {'permille': 23, 'total': 39526}
                }
            },
            '2': {
                '2020': {
                    'color': '#0571b0',
                    'mandates': 22,
                    'name': 'FDP',
                    'voters_count': {
                        'permille': Decimal('181.50'),
                        'total': Decimal('2894.00')
                    },
                    'votes': {'permille': 181, 'total': 309635}
                }
            },
            '3': {
                '2020': {
                    'color': '#0571b0',
                    'mandates': 6,
                    'name': 'GLP',
                    'voters_count': {
                        'permille': Decimal('73.00'),
                        'total': Decimal('1165.00')
                    },
                    'votes': {'permille': 73, 'total': 124660}
                }
            },
            '4': {
                '2020': {
                    'color': '#0571b0',
                    'mandates': 9,
                    'name': 'GRÜ',
                    'voters_count': {
                        'permille': Decimal('89.30'),
                        'total': Decimal('1424.00')
                    },
                    'votes': {'permille': 89, 'total': 152405}
                }
            },
            '5': {
                '2020': {
                    'color': '#0571b0',
                    'mandates': 6,
                    'name': 'SP',
                    'voters_count': {
                        'permille': Decimal('155.60'),
                        'total': Decimal('2481.00')
                    },
                    'votes': {'permille': 156, 'total': 265457}
                }
            },
            '6': {
                '2020': {
                    'color': '#0571b0',
                    'mandates': 35,
                    'name': 'SVP',
                    'voters_count': {
                        'permille': Decimal('258.80'),
                        'total': Decimal('4128.00')
                    },
                    'votes': {'permille': 259, 'total': 441744}
                }
            }
        },
        'request': request,
        'years': ['2020']
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
    assert 'class-for-title' in result
    assert 'class-for-progress' in result
    assert 'class-for-counted-entities' in result
    assert 'class-for-candidates-table' in result
    assert 'class-for-districts-table' in result
    assert 'class-for-list-groups-table' in result
    assert 'class-for-list-groups-chart' in result
    assert 'class-for-number-of-counted-entities' in result
    assert 'class-for-total-entities' in result
    assert 'class-for-last-result-change' in result
    assert 'class-for-seat-allocation-table' in result
    assert 'class-for-seat-allocation-chart' in result
