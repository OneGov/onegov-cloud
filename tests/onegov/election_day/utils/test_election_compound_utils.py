from datetime import date
from onegov.ballot import ElectionCompound
from onegov.election_day.utils.election_compound import get_list_results
from onegov.election_day.utils.election_compound import get_lists_data
from onegov.election_day.utils.election_compound import get_districts_data
from onegov.election_day.utils.election_compound import get_elected_candidates


def test_election_utils_compound(import_test_datasets, election_day_app_sg):
    # Empty
    principal = election_day_app_sg.principal
    session = election_day_app_sg.session()
    session.add(
        ElectionCompound(
            title='Compound', domain='canton', date=date(2020, 3, 8)
        )
    )
    election_compound = session.query(ElectionCompound).one()

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
    assert get_list_results(election_compound, session).all() == [
        ('SVP', 9, 31515),
        ('CVP', 6, 28509),
        ('FDP', 5, 19546),
        ('SP', 4, 17381),
        ('GRÜ', 2, 10027),
        ('GLP', 1, 7725),
        ('EVP', 0, 2834),
        ('FDP_J', 0, 1379)
    ]

    assert get_lists_data(election_compound) == {
        'results': [{
            'class': 'inactive',
            'color': '',
            'text': 'SVP',
            'value': 31515,
            'value2': 9
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'CVP',
            'value': 28509,
            'value2': 6
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'FDP',
            'value': 19546,
            'value2': 5
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'SP',
            'value': 17381,
            'value2': 4
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'GRÜ',
            'value': 10027,
            'value2': 2
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'GLP',
            'value': 7725,
            'value2': 1
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'EVP',
            'value': 2834,
            'value2': 0
        }, {
            'class': 'inactive',
            'color': '',
            'text': 'FDP_J',
            'value': 1379,
            'value2': 0
        }]
    }
    assert get_lists_data(election_compound, mandates_only=True, limit=1,
                          names=['SP', 'Grü']) == {
        'results': [
            {
                'text': 'SP',
                'value': 4,
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
    assert get_list_results(election_compound, session).all() == [
        ('SVP', 9, 87135),
        ('CVP', 6, 71209),
        ('FDP', 5, 55152),
        ('SP', 4, 37291),
        ('GRÜ', 2, 24722),
        ('GLP', 1, 20644),
        ('EVP', 0, 2834),
        ('FDP_J', 0, 1379)
    ]
