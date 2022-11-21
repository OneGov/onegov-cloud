from datetime import date
from decimal import Decimal
from onegov.ballot import ElectionCompound
from onegov.core.utils import Bunch
from onegov.election_day.utils.election_compound import \
    get_candidate_statistics
from onegov.election_day.utils.election_compound import get_districts_data
from onegov.election_day.utils.election_compound import get_elected_candidates
from onegov.election_day.utils.election_compound import get_list_groups
from onegov.election_day.utils.election_compound import get_list_groups_data
from onegov.election_day.utils.parties import get_parties_panachage_data
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_data
from onegov.election_day.utils.parties import get_party_results_deltas


# todo: test superregions with a BL dataset


def test_election_utils_compound(import_test_datasets, election_day_app_sg):
    # Empty
    principal = election_day_app_sg.principal
    session = election_day_app_sg.session()
    session.add(
        ElectionCompound(
            title='Compound', domain='canton', date=date(2020, 3, 8),
            pukelsheim=True, completes_manually=True
        )
    )
    election_compound = session.query(ElectionCompound).one()

    assert get_districts_data(election_compound, principal) == {}
    assert get_elected_candidates(election_compound, session).all() == []
    assert get_candidate_statistics(election_compound) == {}

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
            'link': '',
            'mandates': '0 / 17',
            'percentage': 100.0,
            'progress': '1 / 13',
            'votes': 0
        },
        'Rorschach': {
            'counted': True,
            'entities': [3211, 3213, 3214, 3215, 3216, 3217, 3218, 3219, 3237],
            'link': '',
            'mandates': '0 / 10',
            'percentage': 100.0,
            'progress': '9 / 9',
            'votes': 0
        }
    }
    id_1 = election_1.id
    id_2 = election_2.id
    assert get_elected_candidates(election_compound, session).all() == [
        ('Bruss-Schmidheiny', 'Carmen', '', None, None, 'SVP', '01', id_1),
        ('Eugster', 'Thomas', '', None, None, 'SVP', '01', id_1),
        ('Freund', 'Walter', '', None, None, 'SVP', '01', id_1),
        ('Götte', 'Michael', '', None, None, 'SVP', '01', id_2),
        ('Kuster', 'Peter', '', None, None, 'SVP', '01', id_1),
        ('Luterbacher', 'Mäge', '', None, None, 'SVP', '01', id_2),
        ('Wasserfallen', 'Sandro', '', None, None, 'SVP', '01', id_2),
        ('Willi', 'Christian', '', None, None, 'SVP', '01', id_1),
        ('Wüst', 'Markus', '', None, None, 'SVP', '01', id_1),
        ('Broger', 'Andreas', '', None, None, 'CVP', '02', id_1),
        ('Dürr', 'Patrick', '', None, None, 'CVP', '02', id_1),
        ('Hess', 'Sandro', '', None, None, 'CVP', '02', id_1),
        ('Schöbi', 'Michael', '', None, None, 'CVP', '02', id_1),
        ('Frei', 'Raphael', '', None, None, 'FDP', '02a', id_2),
        ('Raths', 'Robert', '', None, None, 'FDP', '02a', id_2),
        ('Britschgi', 'Stefan', '', None, None, 'FDP', '03', id_1),
        ('Graf', 'Claudia', '', None, None, 'FDP', '03', id_1),
        ('Huber', 'Rolf', '', None, None, 'FDP', '03', id_1),
        ('Bucher', 'Laura', '', None, None, 'SP', '04', id_1),
        ('Gemperli', 'Dominik', '', None, None, 'CVP', '04', id_2),
        ('Krempl-Gnädinger', 'Luzia', '', None, None, 'CVP', '04', id_2),
        ('Maurer', 'Remo', '', None, None, 'SP', '04', id_1),
        ('Etterlin', 'Guido', '', None, None, 'SP', '05', id_2),
        ('Gschwend', 'Meinrad', '', None, None, 'GRÜ', '05', id_1),
        ('Schöb', 'Andrea', '', None, None, 'SP', '05', id_2),
        ('Losa', 'Jeannette', '', None, None, 'GRÜ', '06', id_2),
        ('Mattle', 'Ruedi', '', None, None, 'GLP', '06', id_1)
    ]
    assert get_candidate_statistics(election_compound) == {}

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
    election_compound.manually_completed = True
    session.flush()

    request = Bunch(link=lambda x: f'_{x.domain_segment}')
    assert get_districts_data(election_compound, principal, request) == {
        'Rheintal': {
            'counted': True,
            'entities': [3231, 3232, 3233, 3234, 3235, 3236, 3238, 3251,
                         3252, 3253, 3254, 3255, 3256],
            'link': '_Rheintal',
            'mandates': '17 / 17',
            'percentage': 100.0,
            'progress': '13 / 13',
            'votes': 0
        },
        'Rorschach': {
            'counted': True,
            'entities': [3211, 3213, 3214, 3215, 3216, 3217, 3218, 3219, 3237],
            'link': '_Rorschach',
            'mandates': '10 / 10',
            'percentage': 100.0,
            'progress': '9 / 9',
            'votes': 0
        }
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
        date=date(2014, 1, 1),
        voters_counts=True,
        exact_voters_counts=False
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
    election_compound.completes_manually = True
    election_compound.manually_completed = False
    assert get_list_groups(election_compound) == [
        ('CVP', 931, 22),
        ('SVP', 899, 19),
        ('FDP', 863, 18),
        ('AL', 538, 10),
        ('SP', 418, 7),
        ('GLP', 236, 4),
        ('Piraten', 19, 0)
    ]
    assert get_list_groups_data(election_compound) == {
        'results': [
            {
                'class': 'inactive',
                'color': '#EE7F00',
                'text': 'CVP',
                'value': 931,
                'value2': 22
            },
            {
                'class': 'inactive',
                'color': '#019040',
                'text': 'SVP',
                'value': 899,
                'value2': 19
            },
            {
                'class': 'inactive',
                'color': '#0E52A0',
                'text': 'FDP',
                'value': 863,
                'value2': 18
            },
            {
                'class': 'inactive',
                'color': '#99C040',
                'text': 'AL',
                'value': 538,
                'value2': 10
            },
            {
                'class': 'inactive',
                'color': '#E53136',
                'text': 'SP',
                'value': 418,
                'value2': 7
            },
            {
                'class': 'inactive',
                'color': '#acc700',
                'text': 'GLP',
                'value': 236,
                'value2': 4
            },
            {
                'class': 'inactive',
                'color': '#F9B200',
                'text': 'Piraten',
                'value': 19,
                'value2': 0
            }
        ]
    }

    # Pukelsheim, final
    election_compound.manually_completed = True
    assert get_list_groups(election_compound) == [
        ('CVP', 931, 22),
        ('SVP', 899, 19),
        ('FDP', 863, 18),
        ('AL', 538, 10),
        ('SP', 418, 7),
        ('GLP', 236, 4),
        ('Piraten', 19, 0)
    ]
    assert get_list_groups_data(election_compound) == {
        'results': [
            {
                'class': 'active',
                'color': '#EE7F00',
                'text': 'CVP',
                'value': 931,
                'value2': 22
            },
            {
                'class': 'active',
                'color': '#019040',
                'text': 'SVP',
                'value': 899,
                'value2': 19
            },
            {
                'class': 'active',
                'color': '#0E52A0',
                'text': 'FDP',
                'value': 863,
                'value2': 18
            },
            {
                'class': 'active',
                'color': '#99C040',
                'text': 'AL',
                'value': 538,
                'value2': 10
            },
            {
                'class': 'active',
                'color': '#E53136',
                'text': 'SP',
                'value': 418,
                'value2': 7
            },
            {
                'class': 'active',
                'color': '#acc700',
                'text': 'GLP',
                'value': 236,
                'value2': 4
            },
            {
                'class': 'inactive',
                'color': '#F9B200',
                'text': 'Piraten',
                'value': 19,
                'value2': 0
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
        '0': {
            '2014': {
                'name': 'AL',
                'color': '#99C040',
                'mandates': 10,
                'voters_count': {'permille': Decimal('137.80'), 'total': 538},
                'votes': {'permille': 138, 'total': 43062}
            }
        },
        '1': {
            '2014': {
                'name': 'CVP',
                'color': '#EE7F00',
                'mandates': 22,
                'voters_count': {'permille': Decimal('238.50'), 'total': 931},
                'votes': {'permille': 238, 'total': 74448}
            }
        },
        '2': {
            '2014': {
                'name': 'FDP',
                'color': '#0E52A0',
                'mandates': 18,
                'voters_count': {'permille': Decimal('221.10'), 'total': 863},
                'votes': {'permille': 221, 'total': 69028},
            }
        },
        '3': {
            '2014': {
                'name': 'GLP',
                'color': '#acc700',
                'mandates': 4,
                'voters_count': {'permille': Decimal('60.50'), 'total': 236},
                'votes': {'permille': 60, 'total': 18864}
            }
        },
        '4': {
            '2014': {
                'name': 'Piraten',
                'color': '#F9B200',
                'mandates': 0,
                'voters_count': {'permille': Decimal('4.90'), 'total': 19},
                'votes': {'permille': 5, 'total': 1487}
            }
        },
        '5': {
            '2014': {
                'name': 'SP',
                'color': '#E53136',
                'mandates': 7,
                'voters_count': {'permille': Decimal('107.10'), 'total': 418},
                'votes': {'permille': 107, 'total': 33459}
            }
        },
        '6': {
            '2014': {
                'name': 'SVP',
                'color': '#019040',
                'mandates': 19,
                'voters_count': {'permille': Decimal('230.30'), 'total': 899},
                'votes': {'permille': 230, 'total': 71930}
            }
        }}

    assert get_party_results_deltas(election_compound, years, parties) == (
        False,
        {
            '2014': [
                ['AL', 10, 538, '13.78%'],
                ['CVP', 22, 931, '23.85%'],
                ['FDP', 18, 863, '22.11%'],
                ['GLP', 4, 236, '6.05%'],
                ['Piraten', 0, 19, '0.49%'],
                ['SP', 7, 418, '10.71%'],
                ['SVP', 19, 899, '23.03%']
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
                'value': {'back': 13.78, 'front': 10}
            },
            {
                'active': True,
                'color': '#EE7F00',
                'group': 'CVP',
                'item': '2014',
                'value': {'back': 23.85, 'front': 22}
            },
            {
                'active': True,
                'color': '#0E52A0',
                'group': 'FDP',
                'item': '2014',
                'value': {'back': 22.11, 'front': 18}
            },
            {
                'active': True,
                'color': '#acc700',
                'group': 'GLP',
                'item': '2014',
                'value': {'back': 6.05, 'front': 4}
            },
            {
                'active': True,
                'color': '#F9B200',
                'group': 'Piraten',
                'item': '2014',
                'value': {'back': 0.49, 'front': 0}
            },
            {
                'active': True,
                'color': '#E53136',
                'group': 'SP',
                'item': '2014',
                'value': {'back': 10.71, 'front': 7}
            },
            {
                'active': True,
                'color': '#019040',
                'group': 'SVP',
                'item': '2014',
                'value': {'back': 23.03, 'front': 19}
            }
        ],
        'title': 'Compound'
    }

    # ... with exact voters counts
    election_compound.exact_voters_counts = True

    groups = get_list_groups(election_compound)
    assert groups[0][1] == Decimal('931.00')

    data = get_list_groups_data(election_compound)
    assert data['results'][0]['value'] == 931

    years, parties = get_party_results(election_compound)
    assert parties['0']['2014']['voters_count']['total'] == Decimal('538.00')

    deltas = get_party_results_deltas(election_compound, years, parties)
    assert deltas[1]['2014'][0][2] == Decimal('538.00')

    data = get_party_results_data(election_compound)
    assert data['results'][0]['value']['back'] == 13.78

    # ... with votes
    election_compound.voters_counts = False

    groups = get_list_groups(election_compound)
    assert groups[0][1] == Decimal('931.00')

    data = get_list_groups_data(election_compound)
    assert data['results'][0]['value'] == 931

    years, parties = get_party_results(election_compound)
    assert parties['0']['2014']['votes']['total'] == 43062

    deltas = get_party_results_deltas(election_compound, years, parties)
    assert deltas[1]['2014'][0][2] == 43062

    data = get_party_results_data(election_compound)
    assert data['results'][0]['value']['back'] == 13.8


def test_election_utils_candidate_statistics(
    import_test_datasets, election_day_app_zg
):
    election_compound, errors = import_test_datasets(
        api_format='internal',
        model='election_compound',
        principal='zg',
        domain='municipality',
        domain_segment=(
            'Baar',
            'Cham',
            'Hünenberg',
            'Menzingen',
            'Neuheim',
            'Oberägeri',
            'Risch',
            'Steinhausen',
            'Unterägeri',
            'Walchwil',
            'Zug',
        ),
        number_of_mandates=(
            15,
            10,
            6,
            3,
            2,
            4,
            7,
            6,
            6,
            2,
            19,
        ),
        date_=date(2022, 10, 2),
        dataset_name='kantonsratswahl-2022'
    )

    assert not errors
    assert get_candidate_statistics(election_compound) == {
        'total': {'count': 74, 'age': 55},
        'female': {'count': 23, 'age': 52},
        'male': {'count': 51, 'age': 56}
    }
