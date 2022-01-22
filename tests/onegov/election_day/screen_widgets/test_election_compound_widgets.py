from chameleon import PageTemplate
from datetime import date
from lxml import etree
from onegov.ballot import ElectionCompound
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
    ElectionCompoundListsChartWidget,
    ElectionCompoundListsTableWidget,
    ProgressWidget,
    RowWidget,
    TitleWidget,
)
from tests.onegov.election_day.common import DummyRequest


def test_election_compound_widgets(election_day_app_sg, import_test_datasets):
    structure = """
        <row>
            <column span="1">
                <title class="my-class-1"/>
            </column>
            <column span="1">
                <progress class="my-class-2"/>
            </column>
            <column span="1">
                <counted-entities class="my-class-3"/>
            </column>
            <column span="1">
                <election-compound-candidates-table class="my-class-4"/>
            </column>
            <column span="1">
                <election-compound-districts-table class="my-class-5"/>
            </column>
            <column span="1">
                <election-compound-lists-table class="my-class-6"
                    names="GRÜ   ,  FDP_J     "/>
            </column>
            <column span="1">
                <election-compound-lists-chart class="my-class-7"/>
            </column>
            <column span="1">
                <election-compound-lists-chart class="my-class-8" limit="2"
                    names="a,b"/>
            </column>
            <column span="1">
                <election-compound-list-groups-table class="my-class-9"/>
            </column>
            <column span="1">
                <election-compound-list-groups-chart class="my-class-a"/>
            </column>
        </row>
    """
    widgets = [
        RowWidget(),
        ColumnWidget(),
        CountedEntitiesWidget(),
        ProgressWidget(),
        TitleWidget(),
        ElectionCompoundCandidatesTableWidget(),
        ElectionCompoundDistrictsTableWidget(),
        ElectionCompoundListsChartWidget(),
        ElectionCompoundListsTableWidget(),
        ElectionCompoundListGroupsChartWidget(),
        ElectionCompoundListGroupsTableWidget(),
    ]

    # Empty
    session = election_day_app_sg.session()
    session.add(
        ElectionCompound(
            title='Compound', domain='canton', date=date(2020, 3, 8)
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
        'lists': [],
        'model': model,
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Compound</span>' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result

    # Add intermediate results
    election_1, errors = import_test_datasets(
        'internal',
        'election',
        'sg',
        'district',
        'proporz',
        date_=date(2020, 3, 8),
        number_of_mandates=17,
        domain_segment='Rheintal',
        dataset_name='kantonsratswahl-2020-wahlkreis-rheintal-intermediate',
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
            ('Bruss-Schmidheiny', 'Carmen', '', 'SVP', '01', e_1),
            ('Eugster', 'Thomas', '', 'SVP', '01', e_1),
            ('Freund', 'Walter', '', 'SVP', '01', e_1),
            ('Götte', 'Michael', '', 'SVP', '01', e_2),
            ('Kuster', 'Peter', '', 'SVP', '01', e_1),
            ('Luterbacher', 'Mäge', '', 'SVP', '01', e_2),
            ('Wasserfallen', 'Sandro', '', 'SVP', '01', e_2),
            ('Willi', 'Christian', '', 'SVP', '01', e_1),
            ('Wüst', 'Markus', '', 'SVP', '01', e_1),
            ('Broger', 'Andreas', '', 'CVP', '02', e_1),
            ('Dürr', 'Patrick', '', 'CVP', '02', e_1),
            ('Hess', 'Sandro', '', 'CVP', '02', e_1),
            ('Schöbi', 'Michael', '', 'CVP', '02', e_1),
            ('Frei', 'Raphael', '', 'FDP', '02a', e_2),
            ('Raths', 'Robert', '', 'FDP', '02a', e_2),
            ('Britschgi', 'Stefan', '', 'FDP', '03', e_1),
            ('Graf', 'Claudia', '', 'FDP', '03', e_1),
            ('Huber', 'Rolf', '', 'FDP', '03', e_1),
            ('Bucher', 'Laura', '', 'SP', '04', e_1),
            ('Gemperli', 'Dominik', '', 'CVP', '04', e_2),
            ('Krempl-Gnädinger', 'Luzia', '', 'CVP', '04', e_2),
            ('Maurer', 'Remo', '', 'SP', '04', e_1),
            ('Etterlin', 'Guido', '', 'SP', '05', e_2),
            ('Gschwend', 'Meinrad', '', 'GRÜ', '05', e_1),
            ('Schöb', 'Andrea', '', 'SP', '05', e_2),
            ('Losa', 'Jeannette', '', 'GRÜ', '06', e_2),
            ('Mattle', 'Ruedi', '', 'GLP', '06', e_1)
        ],
        'election': model,
        'election_compound': model,
        'embed': False,
        'entities': 'Rorschach',
        'groups': [],
        'layout': layout,
        'lists': [
            ('SVP', 9, 31515),
            ('CVP', 6, 28509),
            ('FDP', 5, 19546),
            ('SP', 4, 17381),
            ('GRÜ', 2, 10027),
            ('GLP', 1, 7725),
            ('EVP', 0, 2834),
            ('FDP_J', 0, 1379)
        ],
        'model': model,
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Compound</span>' in result
    assert '1 of 2' in result
    assert f'<div>{e_2}</div>'
    assert 'election-compound-candidates-table' in result
    assert 'Bruss-Schmidheiny Carmen' in result
    assert 'election-compound-districts-table' in result
    assert '10 of 10' in result
    assert '9 of 9' in result
    assert '0 of 17' in result
    assert '1 of 13' in result
    assert 'election-compound-lists-table' in result
    assert 'data-text="31515"' not in result
    assert 'data-text="10027"' in result
    assert 'data-text="1379"' in result
    assert (
        'data-dataurl="ElectionCompound/lists-data?limit=0&amp;names="'
    ) in result
    assert (
        'data-dataurl="ElectionCompound/lists-data?limit=02&amp;names=a,b"'
    ) in result
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

    # Add final results
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
            ('Bruss-Schmidheiny', 'Carmen', '', 'SVP', '01', e_1),
            ('Eugster', 'Thomas', '', 'SVP', '01', e_1),
            ('Freund', 'Walter', '', 'SVP', '01', e_1),
            ('Götte', 'Michael', '', 'SVP', '01', e_2),
            ('Kuster', 'Peter', '', 'SVP', '01', e_1),
            ('Luterbacher', 'Mäge', '', 'SVP', '01', e_2),
            ('Wasserfallen', 'Sandro', '', 'SVP', '01', e_2),
            ('Willi', 'Christian', '', 'SVP', '01', e_1),
            ('Wüst', 'Markus', '', 'SVP', '01', e_1),
            ('Broger', 'Andreas', '', 'CVP', '02', e_1),
            ('Dürr', 'Patrick', '', 'CVP', '02', e_1),
            ('Hess', 'Sandro', '', 'CVP', '02', e_1),
            ('Schöbi', 'Michael', '', 'CVP', '02', e_1),
            ('Frei', 'Raphael', '', 'FDP', '02a', e_2),
            ('Raths', 'Robert', '', 'FDP', '02a', e_2),
            ('Britschgi', 'Stefan', '', 'FDP', '03', e_1),
            ('Graf', 'Claudia', '', 'FDP', '03', e_1),
            ('Huber', 'Rolf', '', 'FDP', '03', e_1),
            ('Bucher', 'Laura', '', 'SP', '04', e_1),
            ('Gemperli', 'Dominik', '', 'CVP', '04', e_2),
            ('Krempl-Gnädinger', 'Luzia', '', 'CVP', '04', e_2),
            ('Maurer', 'Remo', '', 'SP', '04', e_1),
            ('Etterlin', 'Guido', '', 'SP', '05', e_2),
            ('Gschwend', 'Meinrad', '', 'GRÜ', '05', e_1),
            ('Schöb', 'Andrea', '', 'SP', '05', e_2),
            ('Losa', 'Jeannette', '', 'GRÜ', '06', e_2),
            ('Mattle', 'Ruedi', '', 'GLP', '06', e_1)
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
        'lists': [
            ('SVP', 9, 87135),
            ('CVP', 6, 71209),
            ('FDP', 5, 55152),
            ('SP', 4, 37291),
            ('GRÜ', 2, 24722),
            ('GLP', 1, 20644),
            ('EVP', 0, 2834),
            ('FDP_J', 0, 1379)
        ],
        'model': model,
        'request': request
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
    assert 'election-compound-lists-table' in result
    assert 'data-text="87135"' not in result
    assert 'data-text="24722"' in result
    assert 'data-text="1379"' in result
    assert 'data-text="3487"' in result
    assert (
        'data-dataurl="ElectionCompound/lists-data?limit=0&amp;names="'
    ) in result
    assert (
        'data-dataurl="ElectionCompound/lists-data?limit=02&amp;names=a,b"'
    ) in result
    assert 'data-dataurl="ElectionCompound/list-groups-data"' in result
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
