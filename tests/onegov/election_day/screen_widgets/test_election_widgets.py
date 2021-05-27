from chameleon import PageTemplate
from datetime import date
from lxml import etree
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ProporzElection
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.screen_widgets import (
    ColumnWidget,
    CountedEntitiesWidget,
    ElectionCandidatesChartWidget,
    ElectionCandidatesTableWidget,
    ElectionCompoundCandidatesTableWidget,
    ElectionCompoundDistrictsTableWidget,
    ElectionCompoundListsChartWidget,
    ElectionCompoundListsTableWidget,
    ElectionListsChartWidget,
    ElectionListsTableWidget,
    ProgressWidget,
    RowWidget,
    TitleWidget,
)
from tests.onegov.election_day.common import DummyRequest


def test_majorz_election_widgets(election_day_app, import_test_datasets):
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
                <election-candidates-table class="my-class-4"/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-5"/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-6" limit="2"/>
            </column>
        </row>
    """
    widgets = [
        RowWidget(),
        ColumnWidget(),
        CountedEntitiesWidget(),
        ProgressWidget(),
        TitleWidget(),
        ElectionCandidatesChartWidget(),
        ElectionCandidatesTableWidget(),
    ]

    # Empty
    session = election_day_app.session()
    session.add(
        Election(title='Election', domain='canton', date=date(2015, 6, 18))
    )
    session.flush()
    model = session.query(Election).one()
    request = DummyRequest(app=election_day_app, session=session)
    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [],
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
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result

    # Add intermediate results
    model, errors = import_test_datasets(
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
    assert not errors
    session.add(model)
    session.flush()

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [
            ('Hegglin', 'Peter', True, '', 10693, None, None),
            ('Eder', 'Joachim', True, '', 10103, None, None),
            ('Brandenberg', 'Manuel', False, '', 4845, None, None),
            ('Gysel', 'Barbara', False, '', 2890, None, None),
            ('Lustenberger', 'Andreas', False, '', 2541, None, None),
            ('Thöni', 'Stefan', False, '', 746, None, None)
        ],
        'election': model,
        'embed': False,
        'entities': 'Baar, Cham, Hünenberg, Menzingen',
        'layout': layout,
        'model': model,
        'request': request,
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert 'majorz_internal_staenderatswahl-2015-intermediate' in result
    assert '4 of 11' in result
    assert 'Baar, Cham, Hünenberg, Menzingen' in result
    assert 'election-candidates-table' in result
    assert 'data-text="10693"' in result
    assert '>n.a.</td>' in result
    assert 'data-dataurl="Election/candidates-data?limit=0"' in result
    assert 'data-dataurl="Election/candidates-data?limit=02"' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result

    # Add final results
    model, errors = import_test_datasets(
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
    assert not errors
    session.add(model)
    session.flush()

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [
            ('Hegglin', 'Peter', True, '', 24132, None, None),
            ('Eder', 'Joachim', True, '', 23620, None, None),
            ('Brandenberg', 'Manuel', False, '', 10997, None, None),
            ('Gysel', 'Barbara', False, '', 6612, None, None),
            ('Lustenberger', 'Andreas', False, '', 5691, None, None),
            ('Thöni', 'Stefan', False, '', 1709, None, None)
        ],
        'election': model,
        'embed': False,
        'entities': (
            'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
            'Steinhausen, Unterägeri, Walchwil, Zug'
        ),
        'layout': layout,
        'model': model,
        'request': request,
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert 'majorz_internal_staenderatswahl-2015' in result
    assert '11 of 11' in result
    assert (
        'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
        'Steinhausen, Unterägeri, Walchwil, Zug'
    ) in result
    assert 'election-candidates-table' in result
    assert 'data-text="24132"' in result
    assert '>n.a.</td>' not in result
    assert 'data-dataurl="Election/candidates-data?limit=0"' in result
    assert 'data-dataurl="Election/candidates-data?limit=02"' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result


def test_proporz_election_widgets(election_day_app, import_test_datasets):
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
                <election-candidates-table class="my-class-4"/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-5"/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-6" limit="2"/>
            </column>
            <column span="1">
                <election-lists-table class="my-class-7"/>
            </column>
            <column span="1">
                <election-lists-chart class="my-class-8"/>
            </column>
            <column span="1">
                <election-lists-chart class="my-class-9" limit="3"/>
            </column>
        </row>
    """
    widgets = [
        RowWidget(),
        ColumnWidget(),
        CountedEntitiesWidget(),
        ProgressWidget(),
        TitleWidget(),
        ElectionCandidatesChartWidget(),
        ElectionCandidatesTableWidget(),
        ElectionListsChartWidget(),
        ElectionListsTableWidget(),
    ]

    # Empty
    session = election_day_app.session()
    session.add(
        ProporzElection(
            title='Election', domain='canton', date=date(2015, 6, 18)
        )
    )
    model = session.query(ProporzElection).one()
    request = DummyRequest(app=election_day_app, session=session)
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
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '>Election</span>' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result

    # Add intermediate results
    model, errors = import_test_datasets(
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
    assert not errors
    session.add(model)
    session.flush()

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [
            ('Lustenberger', 'Andreas', False, '', 1514, 'ALG', '1'),
            ('Estermann', 'Astrid', False, '', 491, 'ALG', '1'),
            ('Schriber-Neiger', 'Hanni', False, '', 423, 'ALG', '1'),
            ('Schuler', 'Hubert', False, '', 1918, 'SP', '10'),
            ('Bürgi Dellsperger', 'Christina', False, '', 1202, 'SP', '10'),
            ('Sivaganesan', 'Rupan', False, '', 691, 'SP', '10'),
            ('Hutter Elsener', 'Simone', False, '', 412, 'SP Frauen', '11'),
            ('Hug', 'Malaika', False, '', 340, 'SP Frauen', '11'),
            ('Mäder Beglinger', 'Anne', False, '', 237, 'SP Frauen', '11'),
            ('Krasnici', 'Denis', False, '', 258, 'SP Juso', '12'),
            ('Spescha', 'Anna', False, '', 202, 'SP Juso', '12'),
            ('Koepfli', 'Virginia', False, '', 102, 'SP Juso', '12'),
            ('Dzaferi', 'Zari', False, '', 1355, 'SP Männer', '13'),
            ('Freimann', 'Fabian', False, '', 218, 'SP Männer', '13'),
            ('Suter', 'Guido', False, '', 188, 'SP Männer', '13'),
            ('Sönmez', 'Sehriban', False, '', 54, 'SP Migrant.', '14'),
            ('Coralic', 'Fadila', False, '', 50, 'SP Migrant.', '14'),
            ('Simsek', 'Deniz', False, '', 38, 'SP Migrant.', '14'),
            ('Aeschi', 'Thomas', True, '', 7731, 'SVP', '15'),
            ('Werner', 'Thomas', False, '', 2914, 'SVP', '15'),
            ('Villiger', 'Thomas', False, '', 2571, 'SVP', '15'),
            ('Pfisterer', 'Luc', False, '', 105, 'SVP Int.', '16'),
            ('Bucher', 'Rinaldo', False, '', 69, 'SVP Int.', '16'),
            ('Hornickel', 'Alexander', False, '', 46, 'SVP Int.', '16'),
            ('Risi', 'Adrian', False, '', 1153, 'SVP WuG', '17'),
            ('Brunner', 'Philip C.', False, '', 471, 'SVP WuG', '17'),
            ('Gertsch', 'Beat', False, '', 268, 'SVP WuG', '17'),
            ('Widmer', 'Fabienne', False, '', 101, 'ALG Junge', '2'),
            ('Gut', 'Christina', False, '', 74, 'ALG Junge', '2'),
            ('Perucchi', 'Alessandro', False, '', 66, 'ALG Junge', '2'),
            ('Haas', 'Esther', False, '', 301, 'ALG Bildung', '3'),
            ('Odermatt', 'Anastas', False, '', 221, 'ALG Bildung', '3'),
            ('Zimmermann Gibson', 'Tabea', False, '', 207, 'ALG Bildung', '3'),
            ('Pfister', 'Gerhard', True, '', 6719, 'CVP', '4'),
            ('Barmet-Schelbert', 'Monika', False, '', 1996, 'CVP', '4'),
            ('Hausheer', 'Andreas', False, '', 1340, 'CVP', '4'),
            ('Bieri', 'Anna', False, '', 2407, 'CVP Junge', '5'),
            ('Iten', 'Christoph', False, '', 587, 'CVP Junge', '5'),
            ('Kremmel', 'Corina', False, '', 525, 'CVP Junge', '5'),
            ('Pezzatti', 'Bruno', True, '', 4309, 'FDP Ost', '6'),
            ('Ingold', 'Gabriela', False, '', 1083, 'FDP Ost', '6'),
            ('Mollet', 'Patrick', False, '', 705, 'FDP Ost', '6'),
            ('Grüter', 'Arno', False, '', 897, 'FDP West', '7'),
            ('Gygli', 'Daniel', False, '', 717, 'FDP West', '7'),
            ('Siegrist', 'Birgitt', False, '', 493, 'FDP West', '7'),
            ('Stadlin', 'Daniel', False, '', 731, 'glp', '8'),
            ('Kottelat Schloesing', 'Michèle', False, '', 508, 'glp', '8'),
            ('Soltermann', 'Claus', False, '', 451, 'glp', '8'),
            ('Mauchle', 'Florian', False, '', 260, 'Piraten', '9'),
            ('Thöni', 'Stefan', False, '', 211, 'Piraten', '9')
        ],
        'election': model,
        'embed': False,
        'entities': 'Baar, Cham, Hünenberg, Menzingen',
        'layout': layout,
        'lists': [
            ('SVP', 13532, '15', 1),
            ('CVP', 10247, '4', 1),
            ('FDP Ost', 6219, '6', 1),
            ('SP', 3866, '10', 0),
            ('CVP Junge', 3549, '5', 0),
            ('ALG', 2459, '1', 0),
            ('FDP West', 2143, '7', 0),
            ('SVP WuG', 1933, '17', 0),
            ('SP Männer', 1814, '13', 0),
            ('glp', 1718, '8', 0),
            ('SP Frauen', 998, '11', 0),
            ('ALG Bildung', 735, '3', 0),
            ('SP Juso', 567, '12', 0),
            ('Piraten', 475, '9', 0),
            ('ALG Junge', 245, '2', 0),
            ('SVP Int.', 223, '16', 0),
            ('SP Migrant.', 146, '14', 0)
        ],
        'model': model,
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert 'proporz_internal_nationalratswahlen-2015-intermediate' in result
    assert '4 of 11' in result
    assert 'Baar, Cham, Hünenberg, Menzingen' in result
    assert 'election-candidates-table' in result
    assert 'data-text="1514"' in result
    assert '>n.a.</td>' in result
    assert 'data-dataurl="ProporzElection/candidates-data?limit=0"' in result
    assert 'data-dataurl="ProporzElection/candidates-data?limit=02"' in result
    assert 'election-lists-table' in result
    assert 'data-text="13532"' in result
    assert 'data-dataurl="ProporzElection/lists-data?limit=0"' in result
    assert 'data-dataurl="ProporzElection/lists-data?limit=03"' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result

    # Add final results
    model, errors = import_test_datasets(
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
    assert not errors
    session.add(model)
    session.flush()

    layout = ElectionLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'candidates': [
            ('Lustenberger', 'Andreas', False, '', 3240, 'ALG', '1'),
            ('Estermann', 'Astrid', False, '', 1327, 'ALG', '1'),
            ('Schriber-Neiger', 'Hanni', False, '', 1206, 'ALG', '1'),
            ('Schuler', 'Hubert', False, '', 3859, 'SP', '10'),
            ('Bürgi Dellsperger', 'Christina', False, '', 2987, 'SP', '10'),
            ('Sivaganesan', 'Rupan', False, '', 1874, 'SP', '10'),
            ('Hutter Elsener', 'Simone', False, '', 929, 'SP Frauen', '11'),
            ('Hug', 'Malaika', False, '', 684, 'SP Frauen', '11'),
            ('Mäder Beglinger', 'Anne', False, '', 561, 'SP Frauen', '11'),
            ('Spescha', 'Anna', False, '', 555, 'SP Juso', '12'),
            ('Krasnici', 'Denis', False, '', 550, 'SP Juso', '12'),
            ('Koepfli', 'Virginia', False, '', 218, 'SP Juso', '12'),
            ('Dzaferi', 'Zari', False, '', 2303, 'SP Männer', '13'),
            ('Suter', 'Guido', False, '', 545, 'SP Männer', '13'),
            ('Freimann', 'Fabian', False, '', 394, 'SP Männer', '13'),
            ('Coralic', 'Fadila', False, '', 144, 'SP Migrant.', '14'),
            ('Sönmez', 'Sehriban', False, '', 117, 'SP Migrant.', '14'),
            ('Simsek', 'Deniz', False, '', 82, 'SP Migrant.', '14'),
            ('Aeschi', 'Thomas', True, '', 17034, 'SVP', '15'),
            ('Werner', 'Thomas', False, '', 7206, 'SVP', '15'),
            ('Villiger', 'Thomas', False, '', 5629, 'SVP', '15'),
            ('Pfisterer', 'Luc', False, '', 269, 'SVP Int.', '16'),
            ('Bucher', 'Rinaldo', False, '', 168, 'SVP Int.', '16'),
            ('Hornickel', 'Alexander', False, '', 132, 'SVP Int.', '16'),
            ('Risi', 'Adrian', False, '', 2607, 'SVP WuG', '17'),
            ('Brunner', 'Philip C.', False, '', 1159, 'SVP WuG', '17'),
            ('Gertsch', 'Beat', False, '', 607, 'SVP WuG', '17'),
            ('Widmer', 'Fabienne', False, '', 345, 'ALG Junge', '2'),
            ('Gut', 'Christina', False, '', 235, 'ALG Junge', '2'),
            ('Perucchi', 'Alessandro', False, '', 222, 'ALG Junge', '2'),
            ('Odermatt', 'Anastas', False, '', 637, 'ALG Bildung', '3'),
            ('Haas', 'Esther', False, '', 559, 'ALG Bildung', '3'),
            ('Zimmermann Gibson', 'Tabea', False, '', 490, 'ALG Bildung', '3'),
            ('Pfister', 'Gerhard', True, '', 16134, 'CVP', '4'),
            ('Barmet-Schelbert', 'Monika', False, '', 4093, 'CVP', '4'),
            ('Hausheer', 'Andreas', False, '', 3606, 'CVP', '4'),
            ('Bieri', 'Anna', False, '', 3908, 'CVP Junge', '5'),
            ('Iten', 'Christoph', False, '', 1394, 'CVP Junge', '5'),
            ('Kremmel', 'Corina', False, '', 1163, 'CVP Junge', '5'),
            ('Pezzatti', 'Bruno', True, '', 10174, 'FDP Ost', '6'),
            ('Ingold', 'Gabriela', False, '', 3637, 'FDP Ost', '6'),
            ('Mollet', 'Patrick', False, '', 2190, 'FDP Ost', '6'),
            ('Grüter', 'Arno', False, '', 1706, 'FDP West', '7'),
            ('Gygli', 'Daniel', False, '', 1378, 'FDP West', '7'),
            ('Siegrist', 'Birgitt', False, '', 1142, 'FDP West', '7'),
            ('Stadlin', 'Daniel', False, '', 1823, 'glp', '8'),
            ('Kottelat Schloesing', 'Michèle', False, '', 1256, 'glp', '8'),
            ('Soltermann', 'Claus', False, '', 1043, 'glp', '8'),
            ('Mauchle', 'Florian', False, '', 629, 'Piraten', '9'),
            ('Thöni', 'Stefan', False, '', 488, 'Piraten', '9')
        ],
        'election': model,
        'embed': False,
        'entities': (
            'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
            'Steinhausen, Unterägeri, Walchwil, Zug'
        ),
        'layout': layout,
        'lists': [
            ('SVP', 30532, '15', 1),
            ('CVP', 24335, '4', 1),
            ('FDP Ost', 16285, '6', 1),
            ('SP', 8868, '10', 0),
            ('CVP Junge', 6521, '5', 0),
            ('ALG', 5844, '1', 0),
            ('SVP WuG', 4436, '17', 0),
            ('FDP West', 4299, '7', 0),
            ('glp', 4178, '8', 0),
            ('SP Männer', 3314, '13', 0),
            ('SP Frauen', 2186, '11', 0),
            ('ALG Bildung', 1701, '3', 0),
            ('SP Juso', 1333, '12', 0),
            ('Piraten', 1128, '9', 0),
            ('ALG Junge', 807, '2', 0),
            ('SVP Int.', 575, '16', 0),
            ('SP Migrant.', 347, '14', 0)
        ],
        'model': model,
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
    assert 'data-text="3240"' in result
    assert '>n.a.</td>' not in result
    assert 'data-dataurl="ProporzElection/candidates-data?limit=0"' in result
    assert 'data-dataurl="ProporzElection/candidates-data?limit=02"' in result
    assert 'election-lists-table' in result
    assert 'data-text="30532"' in result
    assert 'data-dataurl="ProporzElection/lists-data?limit=0"' in result
    assert 'data-dataurl="ProporzElection/lists-data?limit=03"' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result


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
                <election-compound-lists-table class="my-class-6"/>
            </column>
            <column span="1">
                <election-compound-lists-chart class="my-class-7"/>
            </column>
            <column span="1">
                <election-compound-lists-chart class="my-class-8" limit="2"/>
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
    assert 'my-class-8' in result

    # Add intermediate results
    election_1, errors = import_test_datasets(
        'internal',
        'election',
        'sg',
        'region',
        'proporz',
        date_=date(2020, 3, 8),
        number_of_mandates=17,
        dataset_name='kantonsratswahl-2020-wahlkreis-rheintal-intermediate',
        app_session=session
    )
    assert not errors
    election_2, errors = import_test_datasets(
        'internal',
        'election',
        'sg',
        'region',
        'proporz',
        date_=date(2020, 3, 8),
        number_of_mandates=10,
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
        'entities': e_2,
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
    assert 'data-text="31515"' in result
    assert '>n.a.</td>' in result
    assert 'data-dataurl="ElectionCompound/lists-data?limit=0"' in result
    assert 'data-dataurl="ElectionCompound/lists-data?limit=02"' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result

    # Add final results
    election_1, errors = import_test_datasets(
        'internal',
        'election',
        'sg',
        'region',
        'proporz',
        date_=date(2020, 3, 8),
        number_of_mandates=17,
        dataset_name='kantonsratswahl-2020-wahlkreis-rheintal',
        app_session=session
    )
    assert not errors
    session.add(election_1)
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
        'entities': f'{e_1}, {e_2}',
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

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

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
    assert 'data-text="87135"' in result
    assert '>n.a.</td>' not in result
    assert 'data-dataurl="ElectionCompound/lists-data?limit=0"' in result
    assert 'data-dataurl="ElectionCompound/lists-data?limit=02"' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
