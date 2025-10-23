from datetime import date
from decimal import Decimal
from onegov.core.utils import Bunch
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import PartyResult
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
from onegov.election_day.utils.parties import get_party_results_seat_allocation


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
    results = import_test_datasets(
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
    assert len(results) == 1
    election_1, errors = next(iter(results.values()))
    assert not errors
    results = import_test_datasets(
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
    assert len(results) == 1
    election_2, errors = next(iter(results.values()))
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
    results = import_test_datasets(
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
    assert len(results) == 1
    election_1, errors = next(iter(results.values()))
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
    results = import_test_datasets(
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
    assert len(results) == 1
    election, errors = next(iter(results.values()))
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

    results = import_test_datasets(
        'internal',
        'parties',
        'zg',
        'municipality',
        'proporz',
        election=election_compound,
        dataset_name='kantonsratswahl-2014-parteien',
    )
    assert len(results) == 1
    errors = next(iter(results.values()))
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
                'class': 'active',
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

    def assert_link(active, color, source, target, value):
        assert {
            'active': active, 'color': color,
            'source': source, 'target': target, 'value': value
        } in data['links']

    assert_link(True, '#EE7F00', 2, 9, 1797)
    assert_link(True, '#0E52A0', 3, 9, 876)
    assert_link(True, '#acc700', 4, 9, 1336)
    assert_link(False, '#F9B200', 5, 9, 274)
    assert_link(True, '#E53136', 6, 9, 2450)
    assert_link(True, '#019040', 7, 9, 414)
    assert_link(False, None, 0, 9, 5981)
    assert_link(True, '#99C040', 1, 10, 1271)
    assert_link(True, '#0E52A0', 3, 10, 4281)
    assert_link(True, '#acc700', 4, 10, 1128)
    assert_link(False, '#F9B200', 5, 10, 93)
    assert_link(True, '#E53136', 6, 10, 1342)
    assert_link(True, '#019040', 7, 10, 3467)
    assert_link(False, None, 0, 10, 11593)
    assert_link(True, '#99C040', 1, 11, 531)
    assert_link(True, '#EE7F00', 2, 11, 3339)
    assert_link(True, '#acc700', 4, 11, 817)
    assert_link(False, '#F9B200', 5, 11, 129)
    assert_link(True, '#E53136', 6, 11, 678)
    assert_link(True, '#019040', 7, 11, 2979)
    assert_link(False, None, 0, 11, 8289)
    assert_link(True, '#99C040', 1, 12, 570)
    assert_link(True, '#EE7F00', 2, 12, 721)
    assert_link(True, '#0E52A0', 3, 12, 667)
    assert_link(False, '#F9B200', 5, 12, 84)
    assert_link(True, '#E53136', 6, 12, 573)
    assert_link(True, '#019040', 7, 12, 249)
    assert_link(False, None, 0, 12, 2739)
    assert_link(True, '#99C040', 1, 13, 58)
    assert_link(True, '#EE7F00', 2, 13, 32)
    assert_link(True, '#0E52A0', 3, 13, 21)
    assert_link(True, '#acc700', 4, 13, 60)
    assert_link(True, '#E53136', 6, 13, 50)
    assert_link(True, '#019040', 7, 13, 25)
    assert_link(False, None, 0, 13, 227)
    assert_link(True, '#99C040', 1, 14, 1789)
    assert_link(True, '#EE7F00', 2, 14, 1299)
    assert_link(True, '#0E52A0', 3, 14, 581)
    assert_link(True, '#acc700', 4, 14, 840)
    assert_link(False, '#F9B200', 5, 14, 112)
    assert_link(True, '#019040', 7, 14, 342)
    assert_link(False, None, 0, 14, 4623)
    assert_link(True, '#99C040', 1, 15, 160)
    assert_link(True, '#EE7F00', 2, 15, 1724)
    assert_link(True, '#0E52A0', 3, 15, 1990)
    assert_link(True, '#acc700', 4, 15, 256)
    assert_link(False, '#F9B200', 5, 15, 101)
    assert_link(True, '#E53136', 6, 15, 196)
    assert_link(False, None, 0, 15, 7035)

    def assert_node(active, color, id_, name):
        assert {
            'active': active, 'color': color, 'id': id_, 'name': name
        } in data['nodes']

    assert_node(False, None, 1, '-')
    assert_node(True, '#99C040', 2, 'AL')
    assert_node(True, '#EE7F00', 3, 'CVP')
    assert_node(True, '#0E52A0', 4, 'FDP')
    assert_node(True, '#acc700', 5, 'GLP')
    assert_node(False, '#F9B200', 6, 'Piraten')
    assert_node(True, '#E53136', 7, 'SP')
    assert_node(True, '#019040', 8, 'SVP')
    assert_node(False, None, 9, '-')
    assert_node(True, '#99C040', 10, 'AL')
    assert_node(True, '#EE7F00', 11, 'CVP')
    assert_node(True, '#0E52A0', 12, 'FDP')
    assert_node(True, '#acc700', 13, 'GLP')
    assert_node(False, '#F9B200', 14, 'Piraten')
    assert_node(True, '#E53136', 15, 'SP')
    assert_node(True, '#019040', 16, 'SVP')

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

    assert get_party_results_seat_allocation(years, parties) == [
        ['AL', 10],
        ['CVP', 22],
        ['FDP', 18],
        ['GLP', 4],
        ['Piraten', 0],
        ['SP', 7],
        ['SVP', 19]
    ]

    assert get_party_results_data(election_compound, False) == {
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

    assert get_party_results_data(election_compound, True) == {
        'results': [
            {
                'class': 'active',
                'color': '#EE7F00',
                'percentage': False,
                'text': 'CVP',
                'value': 931,
                'value2': 22
            },
            {
                'class': 'active',
                'color': '#019040',
                'percentage': False,
                'text': 'SVP',
                'value': 899,
                'value2': 19
            },
            {
                'class': 'active',
                'color': '#0E52A0',
                'percentage': False,
                'text': 'FDP',
                'value': 863,
                'value2': 18
            },
            {
                'class': 'active',
                'color': '#99C040',
                'percentage': False,
                'text': 'AL',
                'value': 538,
                'value2': 10
            },
            {
                'class': 'active',
                'color': '#E53136',
                'percentage': False,
                'text': 'SP',
                'value': 418,
                'value2': 7
            },
            {
                'class': 'active',
                'color': '#acc700',
                'percentage': False,
                'text': 'GLP',
                'value': 236,
                'value2': 4
            },
            {
                'class': 'inactive',
                'color': '#F9B200',
                'percentage': False,
                'text': 'Piraten',
                'value': 19,
                'value2': 0
            }
        ]
    }

    # ... with exact voters counts
    election_compound.horizontal_party_strengths = False
    election_compound.exact_voters_counts = True

    groups = get_list_groups(election_compound)
    assert groups[0][1] == Decimal('931.00')

    data = get_list_groups_data(election_compound)
    assert data['results'][0]['value'] == 931

    years, parties = get_party_results(election_compound)
    assert parties['0']['2014']['voters_count']['total'] == Decimal('538.00')

    deltas = get_party_results_deltas(election_compound, years, parties)
    assert deltas[1]['2014'][0][2] == Decimal('538.00')

    data = get_party_results_data(election_compound, False)
    assert data['results'][0]['value']['back'] == 13.78

    # ... with votes
    election_compound.horizontal_party_strengths = False
    election_compound.voters_counts = False

    groups = get_list_groups(election_compound)
    assert groups[0][1] == Decimal('931.00')

    data = get_list_groups_data(election_compound)
    assert data['results'][0]['value'] == 931

    years, parties = get_party_results(election_compound)
    assert parties['0']['2014']['votes']['total'] == 43062

    deltas = get_party_results_deltas(election_compound, years, parties)
    assert deltas[1]['2014'][0][2] == 43062

    data = get_party_results_data(election_compound, False)
    assert data['results'][0]['value']['back'] == 13.8

    data = get_party_results_data(election_compound, True)
    assert data['results'][0]['value'] == 74448

    # incomplete data (only check for exceptions)
    election_compound.party_results.append(
        PartyResult(party_id='0', name='AL', year=2011, domain='canton')
    )
    election_compound.party_results.append(
        PartyResult(party_id='7', name='XY', year=2011, domain='canton')
    )
    session.flush()

    years, parties = get_party_results(election_compound)
    get_party_results_deltas(election_compound, years, parties)
    get_party_results_seat_allocation(years, parties)
    get_parties_panachage_data(election_compound)
    get_party_results_data(election_compound, False)
    get_party_results_data(election_compound, True)


def test_election_utils_candidate_statistics(
    import_test_datasets, election_day_app_zg
):
    results = import_test_datasets(
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
        domain_supersegment=11 * [''],
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
    assert len(results) == 1
    election_compound, errors = next(iter(results.values()))

    assert not errors
    assert get_candidate_statistics(election_compound) == {
        'total': {'count': 74, 'age': 55},
        'female': {'count': 23, 'age': 52},
        'male': {'count': 51, 'age': 56}
    }
