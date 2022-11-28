from datetime import date
from decimal import Decimal
from onegov.election_day.utils.common import LastUpdatedOrderedDict
from onegov.election_day.utils.election import get_candidates_data
from onegov.election_day.utils.election import get_candidates_results
from onegov.election_day.utils.election import get_candidates_results_by_entity
from onegov.election_day.utils.election import get_connection_results_api
from onegov.election_day.utils.election import get_list_results
from onegov.election_day.utils.election import get_lists_data
from onegov.election_day.utils.parties import get_parties_panachage_data
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_data
from onegov.election_day.utils.parties import get_party_results_deltas
from tests.onegov.election_day.common import print_errors


def test_election_utils_majorz(import_test_datasets, session):
    election, errors = import_test_datasets(
        'internal',
        'election',
        'zg',
        'canton',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=2,
        dataset_name='staenderatswahl-2015-parties',
        has_expats=False
    )
    assert not errors

    election.absolute_majoriy = 18191
    election.majority_type = 'absolute'
    election.colors = {
        'ALG': '#a74c97',
        'CVP': '#ff6300',
        'FDP': '#4068c8',
        'SP': '#db3c27',
        'SVP': '#3f841a',
    }

    # get_candidates_results
    assert tuple(get_candidates_results(election, session)) == (
        ('Hegglin', 'Peter', True, 'CVP', 24132, Decimal('62.3'), None, None),
        ('Eder', 'Joachim', True, 'FDP', 23620, Decimal('61.0'), None, None),
        ('Brandenberg', 'Manuel', False, 'SVP', 10997, Decimal('28.4'), None,
         None),
        ('Gysel', 'Barbara', False, 'SP', 6612, Decimal('17.1'), None, None),
        ('Lustenberger', 'Andreas', False, 'ALG', 5691, Decimal('14.7'), None,
         None),
        ('Thöni', 'Stefan', False, 'Piraten', 1709, Decimal('4.4'), None, None)
    )

    # get_candidates_data
    expected = [
        {
            'class': 'active',
            'color': '#ff6300',
            'text': 'Hegglin Peter',
            'value': 24132
        },
        {
            'class': 'active',
            'color': '#4068c8',
            'text': 'Eder Joachim',
            'value': 23620
        },
        {
            'class': 'inactive',
            'color': '#3f841a',
            'text': 'Brandenberg Manuel',
            'value': 10997
        },
        {
            'class': 'inactive',
            'color': '#db3c27',
            'text': 'Gysel Barbara',
            'value': 6612
        },
        {
            'class': 'inactive',
            'color': '#a74c97',
            'text': 'Lustenberger Andreas',
            'value': 5691
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'Thöni Stefan',
            'value': 1709
        }
    ]
    assert get_candidates_data(election) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': expected,
    }

    # ... invalid filters
    for limit in (0, None, -3):
        assert get_candidates_data(election, limit=limit) == {
            'majority': 18191,
            'title': 'majorz_internal_staenderatswahl-2015-parties',
            'results': expected,
        }
    for lists in ([], None):
        assert get_candidates_data(election, lists=lists) == {
            'majority': 18191,
            'title': 'majorz_internal_staenderatswahl-2015-parties',
            'results': expected,
        }

    # ... valid filters
    assert get_candidates_data(election, limit=3) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': expected[:3],
    }
    assert get_candidates_data(election, lists=['SP', 'ALG', 'GLP']) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': expected[3:5],
    }
    assert get_candidates_data(election, lists=['ALG', 'SP'],
                               sort_by_lists=True) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': list(reversed(expected[3:5]))
    }
    assert get_candidates_data(election, lists=['FDP', 'CVP', 'SP'],
                               sort_by_lists=True, elected=True) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': list(reversed(expected[0:2])),
    }
    assert get_candidates_data(election, elected=True) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': expected[:2],
    }
    assert get_candidates_data(election, limit=1,
                               lists=['SP', 'ALG', 'GLP']) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': expected[3:4],
    }

    # get_list_results
    assert tuple(get_list_results(election)) == tuple()
    assert tuple(get_list_results(election, limit=0)) == tuple()
    assert tuple(get_list_results(election, limit=None)) == tuple()
    assert tuple(get_list_results(election, limit=3)) == tuple()

    assert get_lists_data(election) == {
        'majority': None,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': [],
    }

    # ... invalid filters
    for limit in (0, None, -3):
        assert get_lists_data(election, limit=limit) == {
            'majority': None,
            'title': 'majorz_internal_staenderatswahl-2015-parties',
            'results': [],
        }

    # ... valid filters
    assert get_lists_data(election, limit=3) == {
        'majority': None,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': [],
    }

    # get_candidates_results_by_entity
    candidates, entities = get_candidates_results_by_entity(election)
    candidates = [candidate[1:] for candidate in candidates]
    assert candidates == [
        ('Brandenberg', 'Manuel', 10997),
        ('Eder', 'Joachim', 23620),
        ('Gysel', 'Barbara', 6612),
        ('Hegglin', 'Peter', 24132),
        ('Lustenberger', 'Andreas', 5691),
        ('Thöni', 'Stefan', 1709)
    ]
    assert entities == [
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

    candidates, entities = get_candidates_results_by_entity(
        election, sort_by_votes=True
    )
    candidates = [candidate[1:] for candidate in candidates]
    assert candidates == [
        ('Hegglin', 'Peter', 24132),
        ('Eder', 'Joachim', 23620),
        ('Brandenberg', 'Manuel', 10997),
        ('Gysel', 'Barbara', 6612),
        ('Lustenberger', 'Andreas', 5691),
        ('Thöni', 'Stefan', 1709)
    ]
    assert entities[0][1] == [
        ('Baar', 'Hegglin', 'Peter', 4207),
        ('Baar', 'Eder', 'Joachim', 4237),
        ('Baar', 'Brandenberg', 'Manuel', 2100),
        ('Baar', 'Gysel', 'Barbara', 1264),
        ('Baar', 'Lustenberger', 'Andreas', 1269),
        ('Baar', 'Thöni', 'Stefan', 320)
    ]


def test_election_utils_proporz(import_test_datasets, session):
    election, errors = import_test_datasets(
        'internal',
        'election',
        'zg',
        'canton',
        'proporz',
        date_=date(2015, 10, 18),
        number_of_mandates=3,
        dataset_name='nationalratswahlen-2015',
        has_expats=False
    )
    assert not errors

    election.colors = {
        'CVP': '#ff6300',
        'SVP': '#3f841a',
    }

    # get_candidates_results
    assert tuple(get_candidates_results(election, session)) == (
        ('Lustenberger', 'Andreas', False, '', 3240, 0, 'ALG', '1'),
        ('Estermann', 'Astrid', False, '', 1327, 0, 'ALG', '1'),
        ('Schriber-Neiger', 'Hanni', False, '', 1206, 0, 'ALG', '1'),
        ('Schuler', 'Hubert', False, '', 3859, 0, 'SP', '10'),
        ('Bürgi Dellsperger', 'Christina', False, '', 2987, 0, 'SP', '10'),
        ('Sivaganesan', 'Rupan', False, '', 1874, 0, 'SP', '10'),
        ('Hutter Elsener', 'Simone', False, '', 929, 0, 'SP Frauen', '11'),
        ('Hug', 'Malaika', False, '', 684, 0, 'SP Frauen', '11'),
        ('Mäder Beglinger', 'Anne', False, '', 561, 0, 'SP Frauen', '11'),
        ('Spescha', 'Anna', False, '', 555, 0, 'SP Juso', '12'),
        ('Krasnici', 'Denis', False, '', 550, 0, 'SP Juso', '12'),
        ('Koepfli', 'Virginia', False, '', 218, 0, 'SP Juso', '12'),
        ('Dzaferi', 'Zari', False, '', 2303, 0, 'SP Männer', '13'),
        ('Suter', 'Guido', False, '', 545, 0, 'SP Männer', '13'),
        ('Freimann', 'Fabian', False, '', 394, 0, 'SP Männer', '13'),
        ('Coralic', 'Fadila', False, '', 144, 0, 'SP Migrant.', '14'),
        ('Sönmez', 'Sehriban', False, '', 117, 0, 'SP Migrant.', '14'),
        ('Simsek', 'Deniz', False, '', 82, 0, 'SP Migrant.', '14'),
        ('Aeschi', 'Thomas', True, '', 17034, 0, 'SVP', '15'),
        ('Werner', 'Thomas', False, '', 7206, 0, 'SVP', '15'),
        ('Villiger', 'Thomas', False, '', 5629, 0, 'SVP', '15'),
        ('Pfisterer', 'Luc', False, '', 269, 0, 'SVP Int.', '16'),
        ('Bucher', 'Rinaldo', False, '', 168, 0, 'SVP Int.', '16'),
        ('Hornickel', 'Alexander', False, '', 132, 0, 'SVP Int.', '16'),
        ('Risi', 'Adrian', False, '', 2607, 0, 'SVP WuG', '17'),
        ('Brunner', 'Philip C.', False, '', 1159, 0, 'SVP WuG', '17'),
        ('Gertsch', 'Beat', False, '', 607, 0, 'SVP WuG', '17'),
        ('Widmer', 'Fabienne', False, '', 345, 0, 'ALG Junge', '2'),
        ('Gut', 'Christina', False, '', 235, 0, 'ALG Junge', '2'),
        ('Perucchi', 'Alessandro', False, '', 222, 0, 'ALG Junge', '2'),
        ('Odermatt', 'Anastas', False, '', 637, 0, 'ALG Bildung', '3'),
        ('Haas', 'Esther', False, '', 559, 0, 'ALG Bildung', '3'),
        ('Zimmermann Gibson', 'Tabea', False, '', 490, 0, 'ALG Bildung', '3'),
        ('Pfister', 'Gerhard', True, '', 16134, 0, 'CVP', '4'),
        ('Barmet-Schelbert', 'Monika', False, '', 4093, 0, 'CVP', '4'),
        ('Hausheer', 'Andreas', False, '', 3606, 0, 'CVP', '4'),
        ('Bieri', 'Anna', False, '', 3908, 0, 'CVP Junge', '5'),
        ('Iten', 'Christoph', False, '', 1394, 0, 'CVP Junge', '5'),
        ('Kremmel', 'Corina', False, '', 1163, 0, 'CVP Junge', '5'),
        ('Pezzatti', 'Bruno', True, '', 10174, 0, 'FDP Ost', '6'),
        ('Ingold', 'Gabriela', False, '', 3637, 0, 'FDP Ost', '6'),
        ('Mollet', 'Patrick', False, '', 2190, 0, 'FDP Ost', '6'),
        ('Grüter', 'Arno', False, '', 1706, 0, 'FDP West', '7'),
        ('Gygli', 'Daniel', False, '', 1378, 0, 'FDP West', '7'),
        ('Siegrist', 'Birgitt', False, '', 1142, 0, 'FDP West', '7'),
        ('Stadlin', 'Daniel', False, '', 1823, 0, 'glp', '8'),
        ('Kottelat Schloesing', 'Michèle', False, '', 1256, 0, 'glp', '8'),
        ('Soltermann', 'Claus', False, '', 1043, 0, 'glp', '8'),
        ('Mauchle', 'Florian', False, '', 629, 0, 'Piraten', '9'),
        ('Thöni', 'Stefan', False, '', 488, 0, 'Piraten', '9')
    )

    # get_candidates_data
    expected = [
        {
            'class': 'active',
            'color': '#3f841a',
            'text': 'Aeschi Thomas',
            'value': 17034
        },
        {
            'class': 'active',
            'color': '#ff6300',
            'text': 'Pfister Gerhard',
            'value': 16134
        },
        {
            'class': 'active',
            'color': None,
            'text': 'Pezzatti Bruno',
            'value': 10174
        }
    ]
    assert get_candidates_data(election) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected,
    }

    # ... invalid filters
    for limit in (0, None, -3):
        assert get_candidates_data(election, limit=limit) == {
            'majority': 0,
            'title': 'proporz_internal_nationalratswahlen-2015',
            'results': expected,
        }
    for lists in ([], None):
        assert get_candidates_data(election, lists=lists) == {
            'majority': 0,
            'title': 'proporz_internal_nationalratswahlen-2015',
            'results': expected,
        }

    # ... valid filters
    assert get_candidates_data(election, limit=2) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected[:2],
    }
    assert get_candidates_data(election, lists=['FDP Ost', 'CVP', 'GLP']) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected[1:],
    }
    assert get_candidates_data(election, lists=['FDP Ost', 'CVP'],
                               sort_by_lists=True) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': list(reversed(expected[1:])),
    }
    assert len(get_candidates_data(election, elected=False)['results']) == 50
    assert get_candidates_data(election, limit=1,
                               lists=['FDP Ost', 'CVP', 'GLP']) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected[1:2],
    }
    assert get_candidates_data(election, limit=2, elected=False,
                               lists=['CVP']) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': [
            {
                'class': 'active',
                'color': '#ff6300',
                'text': 'Pfister Gerhard',
                'value': 16134
            },
            {
                'class': 'inactive',
                'color': '#ff6300',
                'text': 'Barmet-Schelbert Monika',
                'value': 4093
            }
        ]
    }
    assert get_candidates_data(election, lists=['FDP Ost', 'CVP'],
                               sort_by_lists=True, elected=False, limit=4) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': [
            {
                'class': 'active',
                'color': None,
                'text': 'Pezzatti Bruno',
                'value': 10174
            },
            {
                'class': 'inactive',
                'color': None,
                'text': 'Ingold Gabriela',
                'value': 3637
            },
            {
                'class': 'inactive',
                'color': None,
                'text': 'Mollet Patrick',
                'value': 2190
            },
            {
                'class': 'active',
                'color': '#ff6300',
                'text': 'Pfister Gerhard',
                'value': 16134
            }
        ],
    }

    # get_list_results
    expected = (
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
    )
    assert tuple(get_list_results(election)) == expected

    # ... invalid filters
    for limit in (0, None, -3):
        assert tuple(get_list_results(election, limit=limit)) == expected
    for names in ([], None):
        assert tuple(get_list_results(election, names=names)) == expected

    # ... valid filters
    assert tuple(get_list_results(election, limit=3)) == expected[:3]
    names = ['SP Juso', 'SP Alle', 'SP Männer', 'SP Frauen']
    assert tuple(get_list_results(election, names=names)) == tuple(
        (e for e in expected if e[0] in names)
    )
    assert tuple(get_list_results(election, limit=2, names=names)) == tuple(
        (e for e in expected if e[0] in names)
    )[:2]

    # get_lists_data
    expected = [
        {
            'class': 'active',
            'color': '#3f841a',
            'text': 'SVP',
            'value': 30532,
            'value2': 1},
        {
            'class': 'active',
            'color': '#ff6300',
            'text': 'CVP',
            'value': 24335,
            'value2': 1
        },
        {
            'class': 'active',
            'color': None,
            'text': 'FDP Ost',
            'value': 16285,
            'value2': 1
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'SP',
            'value': 8868,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'CVP Junge',
            'value': 6521,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'ALG',
            'value': 5844,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'SVP WuG',
            'value': 4436,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'FDP West',
            'value': 4299,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'glp',
            'value': 4178,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'SP Männer',
            'value': 3314,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'SP Frauen',
            'value': 2186,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'ALG Bildung',
            'value': 1701,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'SP Juso',
            'value': 1333,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'Piraten',
            'value': 1128,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'ALG Junge',
            'value': 807,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'SVP Int.',
            'value': 575,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': None,
            'text': 'SP Migrant.',
            'value': 347,
            'value2': 0
        }
    ]
    assert get_lists_data(election) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected,
    }

    # ... invalid filters
    for limit in (0, None, -3):
        assert get_lists_data(election, limit=limit) == {
            'majority': None,
            'title': 'proporz_internal_nationalratswahlen-2015',
            'results': expected,
        }
    for names in ([], None):
        assert get_lists_data(election, names=names) == {
            'majority': None,
            'title': 'proporz_internal_nationalratswahlen-2015',
            'results': expected,
        }

    # ... valid filters
    assert get_lists_data(election, limit=3) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected[:3],
    }
    names = ['SP Juso', 'SP Alle', 'SP Männer', 'SP Frauen']
    assert get_lists_data(election, names=names) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': [e for e in expected if e['text'] in names],
    }
    assert get_lists_data(election, limit=2, names=names) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': [e for e in expected if e['text'] in names][:2],
    }
    names = ['SP Juso', 'SP Frauen', 'SP Männer']
    assert get_lists_data(election, names=names, sort_by_names=True) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': list(reversed([e for e in expected if e['text'] in names])),
    }


def test_election_utils_parties(import_test_datasets, session):
    election, errors = import_test_datasets(
        'internal',
        'election',
        'zg',
        'canton',
        'proporz',
        date_=date(2015, 10, 18),
        number_of_mandates=3,
        dataset_name='nationalratswahlen-2015',
        has_expats=False
    )
    assert not errors
    errors = import_test_datasets(
        'internal',
        'parties',
        'zg',
        'canton',
        'proporz',
        election=election,
        dataset_name='nationalratswahlen-2015-parteien',
    )
    assert not errors

    years, parties = get_party_results(election)
    assert years == ['2011', '2015']
    assert parties == {
        '0': {
            '2011': {
                'name': 'AL',
                'color': '#a74c97',
                'mandates': 0,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 154, 'total': 17972}
            },
            '2015': {
                'name': 'AL',
                'color': '#a74c97',
                'mandates': 0,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 72, 'total': 8352}
            }
        },
        '1': {
            '2011': {
                'name': 'CVP',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 243, 'total': 28413}
            },
            '2015': {
                'name': 'CVP',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 264, 'total': 30856}
            }
        },
        '2': {
            '2011': {
                'name': 'FDP',
                'color': '#4068c8',
                'mandates': 1,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 192, 'total': 22494}
            },
            '2015': {
                'name': 'FDP',
                'color': '#4068c8',
                'mandates': 1,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 176, 'total': 20584}
            }
        },
        '3': {
            '2011': {
                'name': 'GLP',
                'color': '#aeca00',
                'mandates': 0,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 68, 'total': 7943}
            },
            '2015': {
                'name': 'GLP',
                'color': '#aeca00',
                'mandates': 0,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 36, 'total': 4178}
            }
        },
        '4': {
            '2011': {
                'name': 'SP',
                'color': '#db3c27',
                'mandates': 0,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 53, 'total': 6167}
            },
            '2015': {
                'name': 'SP',
                'color': '#db3c27',
                'mandates': 0,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 138, 'total': 16048}
            }
        },
        '5': {
            '2011': {
                'name': 'SVP',
                'color': '#3f841a',
                'mandates': 1,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 283, 'total': 33116}
            },
            '2015': {
                'name': 'SVP',
                'color': '#3f841a',
                'mandates': 1,
                'voters_count': {'permille': 0, 'total': 0},
                'votes': {'permille': 305, 'total': 35543}
            }
        }
    }

    deltas, results = get_party_results_deltas(election, years, parties)
    assert deltas
    assert results == {
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
    }

    assert get_party_results_data(election) == {
        'axis_units': {'back': '%', 'front': ''},
        'groups': ['AL', 'CVP', 'FDP', 'GLP', 'SP', 'SVP'],
        'labels': ['2011', '2015'],
        'maximum': {'back': 100, 'front': 3},
        'results': [
            {
                'active': True,
                'color': '#a74c97',
                'group': 'AL',
                'item': '2015',
                'value': {'back': 7.2, 'front': 0}
            },
            {
                'active': False,
                'color': '#a74c97',
                'group': 'AL',
                'item': '2011',
                'value': {'back': 15.4, 'front': 0}
            },
            {
                'active': True,
                'color': '#ff6300',
                'group': 'CVP',
                'item': '2015',
                'value': {'back': 26.4, 'front': 1}
            },
            {
                'active': False,
                'color': '#ff6300',
                'group': 'CVP',
                'item': '2011',
                'value': {'back': 24.3, 'front': 1}
            },
            {
                'active': True,
                'color': '#4068c8',
                'group': 'FDP',
                'item': '2015',
                'value': {'back': 17.6, 'front': 1}
            },
            {
                'active': False,
                'color': '#4068c8',
                'group': 'FDP',
                'item': '2011',
                'value': {'back': 19.2, 'front': 1}
            },
            {
                'active': True,
                'color': '#aeca00',
                'group': 'GLP',
                'item': '2015',
                'value': {'back': 3.6, 'front': 0}
            },
            {
                'active': False,
                'color': '#aeca00',
                'group': 'GLP',
                'item': '2011',
                'value': {'back': 6.8, 'front': 0}
            },
            {
                'active': True,
                'color': '#db3c27',
                'group': 'SP',
                'item': '2015',
                'value': {'back': 13.8, 'front': 0}
            },
            {
                'active': False,
                'color': '#db3c27',
                'group': 'SP',
                'item': '2011',
                'value': {'back': 5.3, 'front': 0}
            },
            {
                'active': True,
                'color': '#3f841a',
                'group': 'SVP',
                'item': '2015',
                'value': {'back': 30.5, 'front': 1}
            },
            {
                'active': False,
                'color': '#3f841a',
                'group': 'SVP',
                'item': '2011',
                'value': {'back': 28.3, 'front': 1}
            }
        ],
        'title': 'proporz_internal_nationalratswahlen-2015'
    }

    data = get_parties_panachage_data(election)
    assert data['title'] == 'proporz_internal_nationalratswahlen-2015'

    def assert_link(active, color, source, target, value):
        assert {
            'active': active, 'color': color,
            'source': source, 'target': target, 'value': value
        } in data['links']

    assert_link(True, '#ff6300', 2, 8, 20)
    assert_link(True, '#4068c8', 3, 8, 30)
    assert_link(False, '#aeca00', 4, 8, 40)
    assert_link(False, '#db3c27', 5, 8, 50)
    assert_link(True, '#3f841a', 6, 8, 60)
    assert_link(False, None, 0, 8, 70)
    assert_link(False, '#a74c97', 1, 9, 10)
    assert_link(True, '#4068c8', 3, 9, 31)
    assert_link(False, '#aeca00', 4, 9, 41)
    assert_link(False, '#db3c27', 5, 9, 51)
    assert_link(True, '#3f841a', 6, 9, 61)
    assert_link(False, None, 0, 9, 71)
    assert_link(False, '#a74c97', 1, 10, 11)
    assert_link(True, '#ff6300', 2, 10, 21)
    assert_link(False, '#aeca00', 4, 10, 42)
    assert_link(False, '#db3c27', 5, 10, 52)
    assert_link(True, '#3f841a', 6, 10, 62)
    assert_link(False, None, 0, 10, 72)
    assert_link(False, '#a74c97', 1, 11, 12)
    assert_link(True, '#ff6300', 2, 11, 22)
    assert_link(True, '#4068c8', 3, 11, 32)
    assert_link(False, '#db3c27', 5, 11, 53)
    assert_link(True, '#3f841a', 6, 11, 63)
    assert_link(False, None, 0, 11, 73)
    assert_link(False, '#a74c97', 1, 12, 13)
    assert_link(True, '#ff6300', 2, 12, 23)
    assert_link(True, '#4068c8', 3, 12, 33)
    assert_link(False, '#aeca00', 4, 12, 43)
    assert_link(True, '#3f841a', 6, 12, 64)
    assert_link(False, None, 0, 12, 74)
    assert_link(False, '#a74c97', 1, 13, 14)
    assert_link(True, '#ff6300', 2, 13, 24)
    assert_link(True, '#4068c8', 3, 13, 34)
    assert_link(False, '#aeca00', 4, 13, 44)
    assert_link(False, '#db3c27', 5, 13, 54)
    assert_link(False, None, 0, 13, 75)
    assert_link(True, '#3f841a', 6, 13, 35298)
    assert_link(True, '#ff6300', 2, 9, 30591)
    assert_link(False, '#a74c97', 1, 8, 8082)
    assert_link(False, '#aeca00', 4, 11, 3923)
    assert_link(False, '#db3c27', 5, 12, 15798)
    assert_link(True, '#4068c8', 3, 10, 20324)

    def assert_node(active, color, id_, name):
        assert {
            'active': active, 'color': color, 'id': id_, 'name': name
        } in data['nodes']

    assert_node(False, None, 1, '-')
    assert_node(False, '#a74c97', 2, 'AL')
    assert_node(True, '#ff6300', 3, 'CVP')
    assert_node(True, '#4068c8', 4, 'FDP')
    assert_node(False, '#aeca00', 5, 'GLP')
    assert_node(False, '#db3c27', 6, 'SP')
    assert_node(True, '#3f841a', 7, 'SVP')
    assert_node(False, None, 8, '-')
    assert_node(False, '#a74c97', 9, 'AL')
    assert_node(True, '#ff6300', 10, 'CVP')
    assert_node(True, '#4068c8', 11, 'FDP')
    assert_node(False, '#aeca00', 12, 'GLP')
    assert_node(False, '#db3c27', 13, 'SP')
    assert_node(True, '#3f841a', 14, 'SVP')


def test_get_connection_results_internal(import_test_datasets, session):
    election, errors = import_test_datasets(
        'internal',
        'election',
        'gr',
        'canton',
        election_type='proporz',
        number_of_mandates=5,
        date_=date(2019, 10, 20),
        dataset_name='nationalratswahlen-2019-final',
        app_session=session
    )
    assert not errors
    # These results have been verified by T. Hardegger
    results = get_connection_results_api(election, session)

    assert results['1']['total_votes'] == 23141
    assert results['1']['subconns']['1'] == LastUpdatedOrderedDict({
        'total_votes': 7520,
        'lists': LastUpdatedOrderedDict({
            'BDP Graubünden - Junge BDP Graubünden': 3861,
            'BDP Graubünden': 3659
        })
    })
    assert results['1']['subconns']['2'] == LastUpdatedOrderedDict({
        'total_votes': 4668,
        'lists': LastUpdatedOrderedDict({
            'FDP.Die Liberalen Graubünden - Hauptliste': 1627,
            'Jungfreisinnige Graubünden - FDP-Futuro': 1101,
            'FDP.Die Liberalen GR - Support Gewerbe': 1100,
            'FDP.Die Liberalen GR - Support Gemeindepolitik': 840
        })
    })
    assert results['1']['subconns']['3'] == LastUpdatedOrderedDict({
        'total_votes': 10953,
        'lists': LastUpdatedOrderedDict({
            'CVP Graubünden': 8510,
            'CVP - Die Jungen A': 1380,
            'CVP - Die Jungen 1': 1063
        })
    })
    assert results['2']['total_votes'] == 27497
    assert results['2']['subconns']['1'] == LastUpdatedOrderedDict({
        'total_votes': 20420,
        'lists': LastUpdatedOrderedDict({
            'SP Sozialdemokratische Partei': 15969,
            'SP JUSO Frauen*': 3000,
            'SP JUSO Männer*': 1451
        })
    })
    assert results['2']['lists'] == LastUpdatedOrderedDict({
        'Verda - Grüne Graubünden': 1652
    })


def test_get_connection_results_subconn_ids(import_test_datasets, session):
    election, errors = import_test_datasets(
        'internal',
        'election',
        'sg',
        'canton',
        election_type='proporz',
        number_of_mandates=12,
        date_=date(2019, 10, 20),
        dataset_name='test_nonunique_subconn_ids',
        app_session=session
    )
    print_errors(errors)
    assert not errors
    results = get_connection_results_api(election, session)
    assert results['1']['total_votes'] == 3
    assert results['2']['total_votes'] == 2
    assert results['1']['subconns']['1']['total_votes'] == 2
    assert results['2']['subconns']['1']['total_votes'] == 2


# todo: test on incompleted election
