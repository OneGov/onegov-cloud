from chameleon import PageTemplate
from datetime import date
from lxml import etree
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.screen_widgets import (
    ColumnWidget,
    CountedEntitiesWidget,
    ElectionCandidatesByEntityTableWidget,
    ElectionCandidatesChartWidget,
    ElectionCandidatesTableWidget,
    ElectionListsChartWidget,
    ElectionListsTableWidget,
    ProgressWidget,
    RowWidget,
    TitleWidget,
)
from tests.onegov.election_day.common import DummyRequest


def test_majorz_election_widgets(election_day_app_zg, import_test_datasets):
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
                <election-candidates-table class="my-class-4"
                    lists="SP,
                           Grüne,"/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-5"/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-6" limit="2"
                    lists="x,y" elected="True"/>
            </column>
            <column span="1">
                <election-candidates-by-entity-table class="my-class-7"/>
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
        ElectionCandidatesByEntityTableWidget(),
    ]

    # Empty
    session = election_day_app_zg.session()
    session.add(
        Election(title='Election', domain='canton', date=date(2015, 6, 18))
    )
    session.flush()
    model = session.query(Election).one()
    request = DummyRequest(app=election_day_app_zg, session=session)
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
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result

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
            ('Hegglin', 'Peter', True, 'CVP', 10693, None, None),
            ('Eder', 'Joachim', True, 'FDP', 10103, None, None),
            ('Brandenberg', 'Manuel', False, 'SVP', 4845, None, None),
            ('Gysel', 'Barbara', False, 'SP', 2890, None, None),
            ('Lustenberger', 'Andreas', False, 'Grüne', 2541, None, None),
            ('Thöni', 'Stefan', False, 'Piraten', 746, None, None)
        ],
        'candidates_by_entites': (
            [
                ('Brandenberg', 'Manuel', 4845),
                ('Eder', 'Joachim', 10103),
                ('Gysel', 'Barbara', 2890),
                ('Hegglin', 'Peter', 10693),
                ('Lustenberger', 'Andreas', 2541),
                ('Thöni', 'Stefan', 746)
            ],
            [
                ('Baar', [
                    ('Baar', 'Brandenberg', 'Manuel', 2100),
                    ('Baar', 'Eder', 'Joachim', 4237),
                    ('Baar', 'Gysel', 'Barbara', 1264),
                    ('Baar', 'Hegglin', 'Peter', 4207),
                    ('Baar', 'Lustenberger', 'Andreas', 1269),
                    ('Baar', 'Thöni', 'Stefan', 320)
                ]),
                ('Cham', [
                    ('Cham', 'Brandenberg', 'Manuel', 1404),
                    ('Cham', 'Eder', 'Joachim', 2726),
                    ('Cham', 'Gysel', 'Barbara', 888),
                    ('Cham', 'Hegglin', 'Peter', 2905),
                    ('Cham', 'Lustenberger', 'Andreas', 685),
                    ('Cham', 'Thöni', 'Stefan', 232)
                ]),
                ('Hünenberg', [
                    ('Hünenberg', 'Brandenberg', 'Manuel', 881),
                    ('Hünenberg', 'Eder', 'Joachim', 2098),
                    ('Hünenberg', 'Gysel', 'Barbara', 540),
                    ('Hünenberg', 'Hegglin', 'Peter', 2205),
                    ('Hünenberg', 'Lustenberger', 'Andreas', 397),
                    ('Hünenberg', 'Thöni', 'Stefan', 140)
                ]),
                ('Menzingen', [
                    ('Menzingen', 'Brandenberg', 'Manuel', 460),
                    ('Menzingen', 'Eder', 'Joachim', 1042),
                    ('Menzingen', 'Gysel', 'Barbara', 198),
                    ('Menzingen', 'Hegglin', 'Peter', 1376),
                    ('Menzingen', 'Lustenberger', 'Andreas', 190),
                    ('Menzingen', 'Thöni', 'Stefan', 54)
                ])
            ]
        ),
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
    assert 'data-text="10693"' not in result
    assert 'data-text="2890"' in result
    assert 'data-text="2541"' in result
    assert '>n.a.</td>' in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=0&amp;lists=&amp;elected="'
    ) in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True"'
    ) in result
    assert 'election-candidates-by-entity-table' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result

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
            ('Hegglin', 'Peter', True, 'CVP', 24132, None, None),
            ('Eder', 'Joachim', True, 'FDP', 23620, None, None),
            ('Brandenberg', 'Manuel', False, 'SVP', 10997, None, None),
            ('Gysel', 'Barbara', False, 'SP', 6612, None, None),
            ('Lustenberger', 'Andreas', False, 'Grüne', 5691, None, None),
            ('Thöni', 'Stefan', False, 'Piraten', 1709, None, None)
        ],
        'candidates_by_entites': (
            [
                ('Brandenberg', 'Manuel', 10997),
                ('Eder', 'Joachim', 23620),
                ('Gysel', 'Barbara', 6612),
                ('Hegglin', 'Peter', 24132),
                ('Lustenberger', 'Andreas', 5691),
                ('Thöni', 'Stefan', 1709)
            ],
            [
                ('Baar', [
                    ('Baar', 'Brandenberg', 'Manuel', 2100),
                    ('Baar', 'Eder', 'Joachim', 4237),
                    ('Baar', 'Gysel', 'Barbara', 1264),
                    ('Baar', 'Hegglin', 'Peter', 4207),
                    ('Baar', 'Lustenberger', 'Andreas', 1269),
                    ('Baar', 'Thöni', 'Stefan', 320)
                ]),
                ('Cham', [
                    ('Cham', 'Brandenberg', 'Manuel', 1404),
                    ('Cham', 'Eder', 'Joachim', 2726),
                    ('Cham', 'Gysel', 'Barbara', 888),
                    ('Cham', 'Hegglin', 'Peter', 2905),
                    ('Cham', 'Lustenberger', 'Andreas', 685),
                    ('Cham', 'Thöni', 'Stefan', 232)
                ]),
                ('Hünenberg', [
                    ('Hünenberg', 'Brandenberg', 'Manuel', 881),
                    ('Hünenberg', 'Eder', 'Joachim', 2098),
                    ('Hünenberg', 'Gysel', 'Barbara', 540),
                    ('Hünenberg', 'Hegglin', 'Peter', 2205),
                    ('Hünenberg', 'Lustenberger', 'Andreas', 397),
                    ('Hünenberg', 'Thöni', 'Stefan', 140)
                ]),
                ('Menzingen', [
                    ('Menzingen', 'Brandenberg', 'Manuel', 460),
                    ('Menzingen', 'Eder', 'Joachim', 1042),
                    ('Menzingen', 'Gysel', 'Barbara', 198),
                    ('Menzingen', 'Hegglin', 'Peter', 1376),
                    ('Menzingen', 'Lustenberger', 'Andreas', 190),
                    ('Menzingen', 'Thöni', 'Stefan', 54)
                ]),
                ('Neuheim', [
                    ('Neuheim', 'Brandenberg', 'Manuel', 235),
                    ('Neuheim', 'Eder', 'Joachim', 453),
                    ('Neuheim', 'Gysel', 'Barbara', 92),
                    ('Neuheim', 'Hegglin', 'Peter', 511),
                    ('Neuheim', 'Lustenberger', 'Andreas', 94),
                    ('Neuheim', 'Thöni', 'Stefan', 26)
                ]),
                ('Oberägeri', [
                    ('Oberägeri', 'Brandenberg', 'Manuel', 656),
                    ('Oberägeri', 'Eder', 'Joachim', 1380),
                    ('Oberägeri', 'Gysel', 'Barbara', 191),
                    ('Oberägeri', 'Hegglin', 'Peter', 1276),
                    ('Oberägeri', 'Lustenberger', 'Andreas', 150),
                    ('Oberägeri', 'Thöni', 'Stefan', 72)
                ]),
                ('Risch', [
                    ('Risch', 'Brandenberg', 'Manuel', 1041),
                    ('Risch', 'Eder', 'Joachim', 1797),
                    ('Risch', 'Gysel', 'Barbara', 391),
                    ('Risch', 'Hegglin', 'Peter', 1730),
                    ('Risch', 'Lustenberger', 'Andreas', 362),
                    ('Risch', 'Thöni', 'Stefan', 137)
                ]),
                ('Steinhausen', [
                    ('Steinhausen', 'Brandenberg', 'Manuel', 789),
                    ('Steinhausen', 'Eder', 'Joachim', 1827),
                    ('Steinhausen', 'Gysel', 'Barbara', 523),
                    ('Steinhausen', 'Hegglin', 'Peter', 1883),
                    ('Steinhausen', 'Lustenberger', 'Andreas', 490),
                    ('Steinhausen', 'Thöni', 'Stefan', 171)
                ]),
                ('Unterägeri', [
                    ('Unterägeri', 'Brandenberg', 'Manuel', 860),
                    ('Unterägeri', 'Eder', 'Joachim', 2054),
                    ('Unterägeri', 'Gysel', 'Barbara', 320),
                    ('Unterägeri', 'Hegglin', 'Peter', 1779),
                    ('Unterägeri', 'Lustenberger', 'Andreas', 258),
                    ('Unterägeri', 'Thöni', 'Stefan', 85)
                ]),
                ('Walchwil', [
                    ('Walchwil', 'Brandenberg', 'Manuel', 416),
                    ('Walchwil', 'Eder', 'Joachim', 756),
                    ('Walchwil', 'Gysel', 'Barbara', 151),
                    ('Walchwil', 'Hegglin', 'Peter', 801),
                    ('Walchwil', 'Lustenberger', 'Andreas', 93),
                    ('Walchwil', 'Thöni', 'Stefan', 39)
                ]),
                ('Zug', [
                    ('Zug', 'Brandenberg', 'Manuel', 2155),
                    ('Zug', 'Eder', 'Joachim', 5250),
                    ('Zug', 'Gysel', 'Barbara', 2054),
                    ('Zug', 'Hegglin', 'Peter', 5459),
                    ('Zug', 'Lustenberger', 'Andreas', 1703),
                    ('Zug', 'Thöni', 'Stefan', 433)
                ])
            ]
        ),
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
    assert 'data-text="24132"' not in result
    assert 'data-text="6612"' in result
    assert 'data-text="5691"' in result
    assert '>n.a.</td>' not in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=0&amp;lists=&amp;elected="'
    ) in result
    assert (
        'data-dataurl="Election/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True"'
    ) in result
    assert 'election-candidates-by-entity-table' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result


def test_proporz_election_widgets(election_day_app_zg, import_test_datasets):
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
                <election-candidates-table class="my-class-4"
                    lists="SP Migrant.,,,,SVP Int."/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-5"/>
            </column>
            <column span="1">
                <election-candidates-chart class="my-class-6" limit="2"
                    lists="x,y" elected="True"/>
            </column>
            <column span="1">
                <election-lists-table class="my-class-7"
                    names="SP Männer, SP Frauen,   ALG Junge    "/>
            </column>
            <column span="1">
                <election-lists-chart class="my-class-8"/>
            </column>
            <column span="1">
                <election-lists-chart class="my-class-9" limit="3"
                    names="a,b"/>
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
    session = election_day_app_zg.session()
    session.add(
        ProporzElection(
            title='Election', domain='canton', date=date(2015, 6, 18)
        )
    )
    model = session.query(ProporzElection).one()
    request = DummyRequest(app=election_day_app_zg, session=session)
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
    assert 'data-text="1514"' not in result
    assert 'data-text="54"' in result
    assert 'data-text="50"' in result
    assert 'data-text="105"' in result
    assert 'data-text="69"' in result
    assert '>n.a.</td>' in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=0&amp;lists=&amp;elected="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True"'
    ) in result
    assert 'election-lists-table' in result
    assert 'data-text="13532"' not in result
    assert 'data-text="1814"' in result
    assert 'data-text="998"' in result
    assert 'data-text="245"' in result
    assert (
        'data-dataurl="ProporzElection/lists-data?limit=0&amp;names="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/lists-data?limit=03&amp;names=a,b"'
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
    assert 'data-text="3240"' not in result
    assert 'data-text="144"' in result
    assert 'data-text="117"' in result
    assert 'data-text="269"' in result
    assert 'data-text="168"' in result
    assert '>n.a.</td>' not in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=0&amp;lists=&amp;elected="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/candidates-data'
        '?limit=02&amp;lists=x,y&amp;elected=True"'
    ) in result
    assert 'election-lists-table' in result
    assert 'data-text="30532"' not in result
    assert 'data-text="3314"' in result
    assert 'data-text="2186"' in result
    assert 'data-text="807"' in result
    assert (
        'data-dataurl="ProporzElection/lists-data?limit=0&amp;names="'
    ) in result
    assert (
        'data-dataurl="ProporzElection/lists-data?limit=03&amp;names=a,b"'
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
