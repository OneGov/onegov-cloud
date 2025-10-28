from __future__ import annotations

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
from onegov.election_day.utils.parties import get_party_results_seat_allocation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ..conftest import ImportTestDatasets


def test_election_utils_majorz(
    import_test_datasets: ImportTestDatasets,
    session: Session
) -> None:

    results = import_test_datasets(
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
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors

    election.absolute_majority = 18191
    election.majority_type = 'absolute'
    election.colors = {
        'ALG': '#a74c97',
        'CVP': '#ff6300',
        'FDP': '#4068c8',
        'SP': '#db3c27',
        'SVP': '#3f841a',
    }

    # get_candidates_results
    assert tuple(get_candidates_results(election, session)) == (  # type: ignore[comparison-overlap]
        (24132, 'Hegglin', 'Peter', True, 'CVP', Decimal('62.3'), None, None),
        (23620, 'Eder', 'Joachim', True, 'FDP', Decimal('61.0'), None, None),
        (10997, 'Brandenberg', 'Manuel', False, 'SVP', Decimal('28.4'), None,
         None),
        (6612, 'Gysel', 'Barbara', False, 'SP', Decimal('17.1'), None, None),
        (5691, 'Lustenberger', 'Andreas', False, 'ALG', Decimal('14.7'), None,
         None),
        (1709, 'Thöni', 'Stefan', False, 'Piraten', Decimal('4.4'), None, None)
    )

    entities = ['Baar', 'Cham']
    assert tuple(  # type: ignore[comparison-overlap]
        get_candidates_results(election, session, entities=entities)
    ) == (
        (2905 + 4207, 'Hegglin', 'Peter', True, 'CVP', Decimal('60.2'),
         None, None),
        (2726 + 4237, 'Eder', 'Joachim', True, 'FDP', Decimal('58.9'),
         None, None),
        (1404 + 2100, 'Brandenberg', 'Manuel', False, 'SVP', Decimal('29.6'),
         None, None),
        (1264 + 888, 'Gysel', 'Barbara', False, 'SP', Decimal('18.2'),
         None, None),
        (1269 + 685, 'Lustenberger', 'Andreas', False, 'ALG', Decimal('16.5'),
         None, None),
        (232 + 320, 'Thöni', 'Stefan', False, 'Piraten', Decimal('4.7'),
         None, None)
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
    for lists in ([], None):  # type: ignore[var-annotated]
        assert get_candidates_data(election, lists=lists) == {
            'majority': 18191,
            'title': 'majorz_internal_staenderatswahl-2015-parties',
            'results': expected,
        }
    for entities in ([], None):  # type: ignore[assignment]
        assert get_candidates_data(election, entities=entities) == {
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
    assert get_candidates_data(election, lists=['ALG', 'SP'],
                               entities=['Baar', 'Cham'],
                               sort_by_lists=True) == {
        'majority': 0,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': [
            {
                'class': 'inactive',
                'color': '#a74c97',
                'text': 'Lustenberger Andreas',
                'value': 1269 + 685},
            {
                'class': 'inactive',
                'color': '#db3c27',
                'text': 'Gysel Barbara',
                'value': 1264 + 888
            }
        ]
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
    candidates, candidate_entities = get_candidates_results_by_entity(election)
    assert [candidate[1:] for candidate in candidates] == [
        ('Brandenberg', 'Manuel', 10997),
        ('Eder', 'Joachim', 23620),
        ('Gysel', 'Barbara', 6612),
        ('Hegglin', 'Peter', 24132),
        ('Lustenberger', 'Andreas', 5691),
        ('Thöni', 'Stefan', 1709)
    ]
    assert candidate_entities == [
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

    candidates, candidate_entities = get_candidates_results_by_entity(
        election, sort_by_votes=True
    )
    assert [candidate[1:] for candidate in candidates] == [
        ('Hegglin', 'Peter', 24132),
        ('Eder', 'Joachim', 23620),
        ('Brandenberg', 'Manuel', 10997),
        ('Gysel', 'Barbara', 6612),
        ('Lustenberger', 'Andreas', 5691),
        ('Thöni', 'Stefan', 1709)
    ]
    assert candidate_entities[0][1] == [
        ('Baar', 'Hegglin', 'Peter', 4207),
        ('Baar', 'Eder', 'Joachim', 4237),
        ('Baar', 'Brandenberg', 'Manuel', 2100),
        ('Baar', 'Gysel', 'Barbara', 1264),
        ('Baar', 'Lustenberger', 'Andreas', 1269),
        ('Baar', 'Thöni', 'Stefan', 320)
    ]


def test_election_utils_proporz(
    import_test_datasets: ImportTestDatasets,
    session: Session
) -> None:

    results = import_test_datasets(
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
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors

    election.colors = {
        'CVP': '#ff6300',
        'SVP': '#3f841a',
    }

    # get_candidates_results
    assert tuple(get_candidates_results(election, session)) == (
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
        (490, 'Zimmermann Gibson', 'Tabea', False, '', 0, 'ALG Bildung', '3'),
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
    )

    assert tuple(
        get_candidates_results(election, session, entities=['Baar', 'Cham'])
    )[:2] == (
        (290 + 948, 'Lustenberger', 'Andreas', False, '', 0, 'ALG', '1'),
        (135 + 255, 'Estermann', 'Astrid', False, '', 0, 'ALG', '1'),
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
    for lists in ([], None):  # type: ignore[var-annotated]
        assert get_candidates_data(election, lists=lists) == {
            'majority': 0,
            'title': 'proporz_internal_nationalratswahlen-2015',
            'results': expected,
        }
    for entities in ([], None):  # type: ignore[var-annotated]
        assert get_candidates_data(election, entities=entities) == {
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
    assert len(get_candidates_data(election, elected=False)['results']) == 50  # type: ignore[arg-type]
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
    assert get_candidates_data(election, lists=['ALG'], limit=2,
                               entities=['Baar', 'Cham'], elected=False) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': [
            {
                'class': 'inactive',
                'color': None,
                'text': 'Lustenberger Andreas',
                'value': 290 + 948
            },
            {
                'class': 'inactive',
                'color': None,
                'text': 'Estermann Astrid',
                'value': 135 + 255
            }
        ],
    }

    # get_list_results
    expected_list: tuple[tuple[int, str, int], ...] = (
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
    )
    assert tuple(get_list_results(election)) == expected_list

    # ... invalid filters
    for limit in (0, None, -3):
        assert tuple(get_list_results(election, limit=limit)) == expected_list
    for names in ([], None):  # type: ignore[var-annotated]
        assert tuple(get_list_results(election, names=names)) == expected_list
    for entities in ([], None):
        assert tuple(
            get_list_results(election, entities=entities)) == expected_list

    # ... valid filters
    assert tuple(get_list_results(election, limit=3)) == expected_list[:3]
    names = ['SP Juso', 'SP Alle', 'SP Männer', 'SP Frauen']
    assert tuple(get_list_results(election, names=names)) == tuple(
        (e for e in expected_list if e[1] in names)
    )
    assert tuple(get_list_results(election, limit=2, names=names)) == tuple(
        (e for e in expected_list if e[1] in names)
    )[:2]
    entities = ['Baar', 'Zug']
    assert tuple(
        get_list_results(election, limit=2, names=names, entities=entities)
    ) == ((1133 + 724, 'SP Männer', 0), (579 + 570, 'SP Frauen', 0))

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
    for entities in ([], None):
        assert get_lists_data(election, entities=entities) == {
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
        'results': [e for e in expected if e['text'] in names],  # type: ignore[index]
    }
    assert get_lists_data(election, limit=2, names=names) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': [e for e in expected if e['text'] in names][:2],  # type: ignore[index]
    }
    names = ['SP Juso', 'SP Frauen', 'SP Männer']
    assert get_lists_data(election, names=names, sort_by_names=True) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': list(reversed([e for e in expected if e['text'] in names])),  # type: ignore[index]
    }
    entities = ['Baar', 'Zug']
    assert get_lists_data(
        election, limit=2, names=names, entities=entities
    ) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': [
            {
                'class': 'inactive',
                'color': None,
                'text': 'SP Männer',
                'value': 1133 + 724,
                'value2': 0
            },
            {
                'class': 'inactive',
                'color': None,
                'text': 'SP Frauen',
                'value': 579 + 570,
                'value2': 0
            }
        ],
    }


def test_election_utils_parties(
    import_test_datasets: ImportTestDatasets,
    session: Session
) -> None:

    results = import_test_datasets(
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
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors
    results_ = import_test_datasets(
        'internal',
        'parties',
        'zg',
        'canton',
        election=election,
        dataset_name='nationalratswahlen-2015-parteien',
    )
    assert len(results_) == 1
    errors_ = next(iter(results_.values()))
    assert not errors_

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

    deltas, party_results = get_party_results_deltas(election, years, parties)
    assert deltas
    assert party_results == {
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

    assert get_party_results_seat_allocation(years, parties) == [
        ['AL', 0, 0],
        ['CVP', 1, 1],
        ['FDP', 1, 1],
        ['GLP', 0, 0],
        ['SP', 0, 0],
        ['SVP', 1, 1]
    ]

    assert get_party_results_data(election, False) == {
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
    assert get_party_results_data(election, True) == {
        'results': [
            {
                'class': 'active',
                'color': '#3f841a',
                'percentage': True,
                'text': 'SVP 2015',
                'value': 30.5,
                'value2': 1
            },
            {
                'class': 'inactive',
                'color': '#3f841a',
                'percentage': True,
                'text': '2011',
                'value': 28.3,
                'value2': 1
            },
            {
                'class': 'active',
                'color': '#ff6300',
                'percentage': True,
                'text': 'CVP 2015',
                'value': 26.4,
                'value2': 1
            },
            {
                'class': 'inactive',
                'color': '#ff6300',
                'percentage': True,
                'text': '2011',
                'value': 24.3,
                'value2': 1
            },
            {
                'class': 'active',
                'color': '#4068c8',
                'percentage': True,
                'text': 'FDP 2015',
                'value': 17.6,
                'value2': 1
            },
            {
                'class': 'inactive',
                'color': '#4068c8',
                'percentage': True,
                'text': '2011',
                'value': 19.2,
                'value2': 1
            },
            {
                'class': 'inactive',
                'color': '#db3c27',
                'percentage': True,
                'text': 'SP 2015',
                'value': 13.8,
                'value2': 0
            },
            {
                'class': 'inactive',
                'color': '#db3c27',
                'percentage': True,
                'text': '2011',
                'value': 5.3,
                'value2': 0
            },
            {
                'class': 'inactive',
                'color': '#a74c97',
                'percentage': True,
                'text': 'AL 2015',
                'value': 7.2,
                'value2': 0
            },
            {
                'class': 'inactive',
                'color': '#a74c97',
                'percentage': True,
                'text': '2011',
                'value': 15.4,
                'value2': 0
            },
            {
                'class': 'inactive',
                'color': '#aeca00',
                'percentage': True,
                'text': 'GLP 2015',
                'value': 3.6,
                'value2': 0
            },
            {
                'class': 'inactive',
                'color': '#aeca00',
                'percentage': True,
                'text': '2011',
                'value': 6.8,
                'value2': 0
            }
        ]
    }

    data = get_parties_panachage_data(election)
    assert data['title'] == 'proporz_internal_nationalratswahlen-2015'

    def assert_link(
        active: bool,
        color: str | None,
        source: int,
        target: int,
        value: int
    ) -> None:
        assert {  # type: ignore[operator]
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

    def assert_node(
        active: bool,
        color: str | None,
        id_: int,
        name: str
    ) -> None:
        assert {  # type: ignore[operator]
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

    # incomplete data (only check for exceptions)
    party_result = next((
        r for r in election.party_results if r.year == 2011 and r.name == 'AL'
    ))
    party_result.party_id = 'AL11'
    party_result.party_id = '6'
    election.party_results = [
        result for result in election.party_results
        if not (
            (result.year == 2011 and result.name == 'FDP')
            or (result.year == 2015 and result.name == 'CVP')
        )
    ]

    years, parties = get_party_results(election)
    get_party_results_deltas(election, years, parties)
    get_party_results_seat_allocation(years, parties)
    get_parties_panachage_data(election)
    get_party_results_data(election, True)
    get_party_results_data(election, False)


def test_get_connection_results_internal(
    import_test_datasets: ImportTestDatasets,
    session: Session
) -> None:

    import_results = import_test_datasets(
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
    assert len(import_results) == 1
    election, errors = next(iter(import_results.values()))
    assert not errors
    # These results have been verified by T. Hardegger
    results = get_connection_results_api(election, session)

    assert isinstance(results, dict)
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


def test_get_connection_results_subconn_ids(
    import_test_datasets: ImportTestDatasets,
    session: Session
) -> None:

    import_results = import_test_datasets(
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
    assert len(import_results) == 1
    election, errors = next(iter(import_results.values()))
    assert not errors
    results = get_connection_results_api(election, session)
    assert isinstance(results, dict)
    assert results['1']['total_votes'] == 3
    assert results['2']['total_votes'] == 2
    assert results['1']['subconns']['1']['total_votes'] == 2
    assert results['2']['subconns']['1']['total_votes'] == 2


# TODO: test on uncompleted election
