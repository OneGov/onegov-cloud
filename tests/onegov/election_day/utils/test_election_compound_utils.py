from datetime import date
from onegov.ballot import ElectionCompound
from onegov.election_day.utils.election import get_parties_panachage_data
from onegov.election_day.utils.election import get_party_results
from onegov.election_day.utils.election import get_party_results_data
from onegov.election_day.utils.election import get_party_results_deltas
from onegov.election_day.utils.election_compound import get_districts_data
from onegov.election_day.utils.election_compound import get_elected_candidates
from onegov.election_day.utils.election_compound import get_list_groups
from onegov.election_day.utils.election_compound import get_list_groups_data
from onegov.election_day.utils.election_compound import get_list_results
from onegov.election_day.utils.election_compound import get_lists_data


def test_election_utils_compound(import_test_datasets, election_day_app_sg):
    # Empty
    principal = election_day_app_sg.principal
    session = election_day_app_sg.session()
    session.add(
        ElectionCompound(
            title='Compound', domain='canton', date=date(2020, 3, 8),
            pukelsheim=True
        )
    )
    election_compound = session.query(ElectionCompound).one()

    assert get_districts_data(election_compound, principal) == {}
    assert get_elected_candidates(election_compound, session).all() == []
    assert get_list_results(election_compound) == []
    assert get_lists_data(election_compound) == {'results': []}

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
    election_compound.elections = [election_1, election_2]
    session.flush()

    assert get_districts_data(election_compound, principal) == {
        'Rheintal': {
            'counted': False,
            'entities': [3231, 3232, 3233, 3234, 3235, 3236, 3238, 3251,
                         3252, 3253, 3254, 3255, 3256],
            'percentage': 100.0,
            'votes': 0
        },
        'Rorschach': {
            'counted': True,
            'entities': [3211, 3213, 3214, 3215, 3216, 3217, 3218, 3219, 3237],
            'percentage': 100.0,
            'votes': 0
        }
    }
    assert get_elected_candidates(election_compound, session).all() == [
        ('Bruss-Schmidheiny', 'Carmen', '', 'SVP', '01', election_1.id),
        ('Eugster', 'Thomas', '', 'SVP', '01', election_1.id),
        ('Freund', 'Walter', '', 'SVP', '01', election_1.id),
        ('Götte', 'Michael', '', 'SVP', '01', election_2.id),
        ('Kuster', 'Peter', '', 'SVP', '01', election_1.id),
        ('Luterbacher', 'Mäge', '', 'SVP', '01', election_2.id),
        ('Wasserfallen', 'Sandro', '', 'SVP', '01', election_2.id),
        ('Willi', 'Christian', '', 'SVP', '01', election_1.id),
        ('Wüst', 'Markus', '', 'SVP', '01', election_1.id),
        ('Broger', 'Andreas', '', 'CVP', '02', election_1.id),
        ('Dürr', 'Patrick', '', 'CVP', '02', election_1.id),
        ('Hess', 'Sandro', '', 'CVP', '02', election_1.id),
        ('Schöbi', 'Michael', '', 'CVP', '02', election_1.id),
        ('Frei', 'Raphael', '', 'FDP', '02a', election_2.id),
        ('Raths', 'Robert', '', 'FDP', '02a', election_2.id),
        ('Britschgi', 'Stefan', '', 'FDP', '03', election_1.id),
        ('Graf', 'Claudia', '', 'FDP', '03', election_1.id),
        ('Huber', 'Rolf', '', 'FDP', '03', election_1.id),
        ('Bucher', 'Laura', '', 'SP', '04', election_1.id),
        ('Gemperli', 'Dominik', '', 'CVP', '04', election_2.id),
        ('Krempl-Gnädinger', 'Luzia', '', 'CVP', '04', election_2.id),
        ('Maurer', 'Remo', '', 'SP', '04', election_1.id),
        ('Etterlin', 'Guido', '', 'SP', '05', election_2.id),
        ('Gschwend', 'Meinrad', '', 'GRÜ', '05', election_1.id),
        ('Schöb', 'Andrea', '', 'SP', '05', election_2.id),
        ('Losa', 'Jeannette', '', 'GRÜ', '06', election_2.id),
        ('Mattle', 'Ruedi', '', 'GLP', '06', election_1.id)
    ]
    assert get_list_results(election_compound) == [
        ('SVP', 9, 2702),
        ('CVP', 6, 2399),
        ('FDP', 5, 1780),
        ('SP', 4, 1567),
        ('GRÜ', 2, 841),
        ('GLP', 1, 652),
        ('EVP', 0, 283),
        ('FDP_J', 0, 140)
    ]
    assert get_lists_data(election_compound) == {
        'results': [{
            'class': 'inactive',
            'color': '',
            'text': 'SVP',
            'value': 2702,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'CVP',
            'value': 2399,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'FDP',
            'value': 1780,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'SP',
            'value': 1567,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'GRÜ',
            'value': 841,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'GLP',
            'value': 652,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'EVP',
            'value': 283,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'FDP_J',
            'value': 140,
            'value2': None
        }]
    }
    assert get_lists_data(election_compound, limit=1, names=['SP', 'Grü']) == {
        'results': [
            {
                'text': 'SP',
                'value': 1567,
                'value2': None,
                'class': 'inactive',
                'color': ''
            }
        ]
    }

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
    session.add(election_1)
    election_compound.elections = [election_1, election_2]
    election_compound.pukelsheim_completed = True
    session.flush()

    assert get_districts_data(election_compound, principal) == {
        'Rheintal': {
            'counted': True,
            'entities': [3231, 3232, 3233, 3234, 3235, 3236, 3238, 3251,
                         3252, 3253, 3254, 3255, 3256],
            'percentage': 100.0,
            'votes': 0
        },
        'Rorschach': {
            'counted': True,
            'entities': [3211, 3213, 3214, 3215, 3216, 3217, 3218, 3219, 3237],
            'percentage': 100.0,
            'votes': 0
        }
    }
    assert get_list_results(election_compound) == [
        ('SVP', 9, 5973),
        ('CVP', 6, 4911),
        ('FDP', 5, 3874),
        ('SP', 4, 2737),
        ('GRÜ', 2, 1705),
        ('GLP', 1, 1412),
        ('EVP', 0, 283),
        ('FDP_J', 0, 140)
    ]
    assert get_lists_data(election_compound) == {
        'results': [{
            'class': 'active',
            'color': '',
            'text': 'SVP',
            'value': 9,
            'value2': None
        }, {
            'class': 'active',
            'color': '',
            'text': 'CVP',
            'value': 6,
            'value2': None
        }, {
            'class': 'active',
            'color': '',
            'text': 'FDP',
            'value': 5,
            'value2': None
        }, {
            'class': 'active',
            'color': '',
            'text': 'SP',
            'value': 4,
            'value2': None
        }, {
            'class': 'active',
            'color': '',
            'text': 'GRÜ',
            'value': 2,
            'value2': None
        }, {
            'class': 'active',
            'color': '',
            'text': 'GLP',
            'value': 1,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'EVP',
            'value': 0,
            'value2': None
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'FDP_J',
            'value': 0,
            'value2': None
        }]
    }
    assert get_lists_data(election_compound, limit=1, names=['SP', 'Grü']) == {
        'results': [
            {
                'text': 'SP',
                'value': 4,
                'value2': None,
                'class': 'active',
                'color': ''
            }
        ]
    }


def test_election_compound_utils_parties(import_test_datasets, session):
    election, errors = import_test_datasets(
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
    session.add(election)

    election_compound = ElectionCompound(
        title='Compound',
        domain='canton',
        date=date(2014, 1, 1)
    )
    election_compound.elections = [election]
    session.add(election_compound)

    errors = import_test_datasets(
        'internal',
        'parties',
        'zg',
        'municipality',
        'proporz',
        election=election_compound,
        dataset_name='kantonsratswahl-2014-parteien',
    )
    assert not errors

    # Not pukelsheim
    assert len(get_list_groups(election_compound)) == 0
    assert get_list_groups_data(election_compound) == {'results': []}

    # Pukelsheim, intermediate
    election_compound.pukelsheim = True
    assert len(get_list_groups(election_compound)) == 7
    assert get_list_groups_data(election_compound) == {
        'results': [
            {
                'class': 'inactive',
                'color': '#EE7F00',
                'text': 'CVP',
                'value': 931,
                'value2': None
            },
            {
                'class': 'inactive',
                'color': '#019040',
                'text': 'SVP',
                'value': 899,
                'value2': None
            },
            {
                'class': 'inactive',
                'color': '#0E52A0',
                'text': 'FDP',
                'value': 863,
                'value2': None
            },
            {
                'class': 'inactive',
                'color': '#99C040',
                'text': 'AL',
                'value': 538,
                'value2': None
            },
            {
                'class': 'inactive',
                'color': '#E53136',
                'text': 'SP',
                'value': 418,
                'value2': None
            },
            {
                'class': 'inactive',
                'color': '#acc700',
                'text': 'GLP',
                'value': 236,
                'value2': None
            },
            {
                'class': 'inactive',
                'color': '#F9B200',
                'text': 'Piraten',
                'value': 19,
                'value2': None
            }
        ]
    }

    # Pukelsheim, final
    election_compound.pukelsheim_completed = True
    assert get_list_groups_data(election_compound) == {
        'results': [
            {
                'class': 'active',
                'color': '#EE7F00',
                'text': 'CVP',
                'value': 22,
                'value2': None
            },
            {
                'class': 'active',
                'color': '#019040',
                'text': 'SVP',
                'value': 19,
                'value2': None
            },
            {
                'class': 'active',
                'color': '#0E52A0',
                'text': 'FDP',
                'value': 18,
                'value2': None
            },
            {
                'class': 'active',
                'color': '#99C040',
                'text': 'AL',
                'value': 10,
                'value2': None
            },
            {
                'class': 'active',
                'color': '#E53136',
                'text': 'SP',
                'value': 7,
                'value2': None
            },
            {
                'class': 'active',
                'color': '#acc700',
                'text': 'GLP',
                'value': 4,
                'value2': None
            },
            {
                'class': 'inactive',
                'color': '#F9B200',
                'text': 'Piraten',
                'value': 0,
                'value2': None
            }
        ]
    }

    # Party results
    data = get_parties_panachage_data(election_compound)
    assert data['title'] == 'Compound'
    l = data['links']
    assert {'color': '#EE7F00', 'source': 2, 'target': 9, 'value': 1797} in l
    assert {'color': '#0E52A0', 'source': 3, 'target': 9, 'value': 876} in l
    assert {'color': '#acc700', 'source': 4, 'target': 9, 'value': 1336} in l
    assert {'color': '#F9B200', 'source': 5, 'target': 9, 'value': 274} in l
    assert {'color': '#E53136', 'source': 6, 'target': 9, 'value': 2450} in l
    assert {'color': '#019040', 'source': 7, 'target': 9, 'value': 414} in l
    assert {'color': '#999', 'source': 0, 'target': 9, 'value': 5981} in l
    assert {'color': '#99C040', 'source': 1, 'target': 10, 'value': 1271} in l
    assert {'color': '#0E52A0', 'source': 3, 'target': 10, 'value': 4281} in l
    assert {'color': '#acc700', 'source': 4, 'target': 10, 'value': 1128} in l
    assert {'color': '#F9B200', 'source': 5, 'target': 10, 'value': 93} in l
    assert {'color': '#E53136', 'source': 6, 'target': 10, 'value': 1342} in l
    assert {'color': '#019040', 'source': 7, 'target': 10, 'value': 3467} in l
    assert {'color': '#999', 'source': 0, 'target': 10, 'value': 11593} in l
    assert {'color': '#99C040', 'source': 1, 'target': 11, 'value': 531} in l
    assert {'color': '#EE7F00', 'source': 2, 'target': 11, 'value': 3339} in l
    assert {'color': '#acc700', 'source': 4, 'target': 11, 'value': 817} in l
    assert {'color': '#F9B200', 'source': 5, 'target': 11, 'value': 129} in l
    assert {'color': '#E53136', 'source': 6, 'target': 11, 'value': 678} in l
    assert {'color': '#019040', 'source': 7, 'target': 11, 'value': 2979} in l
    assert {'color': '#999', 'source': 0, 'target': 11, 'value': 8289} in l
    assert {'color': '#99C040', 'source': 1, 'target': 12, 'value': 570} in l
    assert {'color': '#EE7F00', 'source': 2, 'target': 12, 'value': 721} in l
    assert {'color': '#0E52A0', 'source': 3, 'target': 12, 'value': 667} in l
    assert {'color': '#F9B200', 'source': 5, 'target': 12, 'value': 84} in l
    assert {'color': '#E53136', 'source': 6, 'target': 12, 'value': 573} in l
    assert {'color': '#019040', 'source': 7, 'target': 12, 'value': 249} in l
    assert {'color': '#999', 'source': 0, 'target': 12, 'value': 2739} in l
    assert {'color': '#99C040', 'source': 1, 'target': 13, 'value': 58} in l
    assert {'color': '#EE7F00', 'source': 2, 'target': 13, 'value': 32} in l
    assert {'color': '#0E52A0', 'source': 3, 'target': 13, 'value': 21} in l
    assert {'color': '#acc700', 'source': 4, 'target': 13, 'value': 60} in l
    assert {'color': '#E53136', 'source': 6, 'target': 13, 'value': 50} in l
    assert {'color': '#019040', 'source': 7, 'target': 13, 'value': 25} in l
    assert {'color': '#999', 'source': 0, 'target': 13, 'value': 227} in l
    assert {'color': '#99C040', 'source': 1, 'target': 14, 'value': 1789} in l
    assert {'color': '#EE7F00', 'source': 2, 'target': 14, 'value': 1299} in l
    assert {'color': '#0E52A0', 'source': 3, 'target': 14, 'value': 581} in l
    assert {'color': '#acc700', 'source': 4, 'target': 14, 'value': 840} in l
    assert {'color': '#F9B200', 'source': 5, 'target': 14, 'value': 112} in l
    assert {'color': '#019040', 'source': 7, 'target': 14, 'value': 342} in l
    assert {'color': '#999', 'source': 0, 'target': 14, 'value': 4623} in l
    assert {'color': '#99C040', 'source': 1, 'target': 15, 'value': 160} in l
    assert {'color': '#EE7F00', 'source': 2, 'target': 15, 'value': 1724} in l
    assert {'color': '#0E52A0', 'source': 3, 'target': 15, 'value': 1990} in l
    assert {'color': '#acc700', 'source': 4, 'target': 15, 'value': 256} in l
    assert {'color': '#F9B200', 'source': 5, 'target': 15, 'value': 101} in l
    assert {'color': '#E53136', 'source': 6, 'target': 15, 'value': 196} in l
    assert {'color': '#999', 'source': 0, 'target': 15, 'value': 7035} in l
    assert {'color': '#0E52A0', 'source': 3, 'target': 11, 'value': 52266} in l
    assert {'color': '#E53136', 'source': 6, 'target': 14, 'value': 23873} in l
    assert {'color': '#019040', 'source': 7, 'target': 15, 'value': 60468} in l
    assert {'color': '#F9B200', 'source': 5, 'target': 13, 'value': 1014} in l
    assert {'color': '#99C040', 'source': 1, 'target': 9, 'value': 29934} in l
    assert {'color': '#EE7F00', 'source': 2, 'target': 10, 'value': 51273} in l
    assert {'color': '#acc700', 'source': 4, 'target': 12, 'value': 13261} in l
    n = data['nodes']
    assert {'color': '#999', 'id': 1, 'name': '-'} in n
    assert {'color': '#99C040', 'id': 2, 'name': 'AL'} in n
    assert {'color': '#EE7F00', 'id': 3, 'name': 'CVP'} in n
    assert {'color': '#0E52A0', 'id': 4, 'name': 'FDP'} in n
    assert {'color': '#acc700', 'id': 5, 'name': 'GLP'} in n
    assert {'color': '#F9B200', 'id': 6, 'name': 'Piraten'} in n
    assert {'color': '#E53136', 'id': 7, 'name': 'SP'} in n
    assert {'color': '#019040', 'id': 8, 'name': 'SVP'} in n
    assert {'color': '#999', 'id': 9, 'name': '-'} in n
    assert {'color': '#99C040', 'id': 10, 'name': 'AL'} in n
    assert {'color': '#EE7F00', 'id': 11, 'name': 'CVP'} in n
    assert {'color': '#0E52A0', 'id': 12, 'name': 'FDP'} in n
    assert {'color': '#acc700', 'id': 13, 'name': 'GLP'} in n
    assert {'color': '#F9B200', 'id': 14, 'name': 'Piraten'} in n
    assert {'color': '#E53136', 'id': 15, 'name': 'SP'} in n
    assert {'color': '#019040', 'id': 16, 'name': 'SVP'} in n

    years, parties = get_party_results(election_compound)
    assert years == ['2014']
    assert parties == {
        'AL': {
            '2014': {
                'color': '#99C040',
                'mandates': 10,
                'voters_count': 538,
                'votes': {'permille': 138, 'total': 43062}
            }
        },
        'CVP': {
            '2014': {
                'color': '#EE7F00',
                'mandates': 22,
                'voters_count': 931,
                'votes': {'permille': 238, 'total': 74448}
            }
        },
        'FDP': {
            '2014': {
                'color': '#0E52A0',
                'mandates': 18,
                'voters_count': 863,
                'votes': {'permille': 221, 'total': 69028}
            }
        },
        'GLP': {
            '2014': {
                'color': '#acc700',
                'mandates': 4,
                'voters_count': 236,
                'votes': {'permille': 60, 'total': 18864}
            }
        },
        'Piraten': {
            '2014': {
                'color': '#F9B200',
                'mandates': 0,
                'voters_count': 19,
                'votes': {'permille': 5, 'total': 1487}
            }
        },
        'SP': {
            '2014': {
                'color': '#E53136',
                'mandates': 7,
                'voters_count': 418,
                'votes': {'permille': 107, 'total': 33459}
            }
        },
        'SVP': {
            '2014': {
                'color': '#019040',
                'mandates': 19,
                'voters_count': 899,
                'votes': {'permille': 230, 'total': 71930}
            }
        }}

    assert get_party_results_deltas(election_compound, years, parties) == (
        False,
        {
            '2014': [
                ['AL', 10, 538, 43062, '13.8%'],
                ['CVP', 22, 931, 74448, '23.8%'],
                ['FDP', 18, 863, 69028, '22.1%'],
                ['GLP', 4, 236, 18864, '6.0%'],
                ['Piraten', 0, 19, 1487, '0.5%'],
                ['SP', 7, 418, 33459, '10.7%'],
                ['SVP', 19, 899, 71930, '23.0%']
            ]
        }
    )

    assert get_party_results_data(election_compound) == {
        'axis_units': {'back': '%', 'front': ''},
        'groups': ['AL', 'CVP', 'FDP', 'GLP', 'Piraten', 'SP', 'SVP'],
        'labels': ['2014'],
        'maximum': {'back': 100, 'front': 17},
        'results': [
            {
                'active': True,
                'color': '#99C040',
                'group': 'AL',
                'item': '2014',
                'value': {'back': 13.8, 'front': 10}
            },
            {
                'active': True,
                'color': '#EE7F00',
                'group': 'CVP',
                'item': '2014',
                'value': {'back': 23.8, 'front': 22}
            },
            {
                'active': True,
                'color': '#0E52A0',
                'group': 'FDP',
                'item': '2014',
                'value': {'back': 22.1, 'front': 18}
            },
            {
                'active': True,
                'color': '#acc700',
                'group': 'GLP',
                'item': '2014',
                'value': {'back': 6.0, 'front': 4}
            },
            {
                'active': True,
                'color': '#F9B200',
                'group': 'Piraten',
                'item': '2014',
                'value': {'back': 0.5, 'front': 0}
            },
            {
                'active': True,
                'color': '#E53136',
                'group': 'SP',
                'item': '2014',
                'value': {'back': 10.7, 'front': 7}
            },
            {
                'active': True,
                'color': '#019040',
                'group': 'SVP',
                'item': '2014',
                'value': {'back': 23.0, 'front': 19}
            }
        ],
        'title': 'Compound'
    }
