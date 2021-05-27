from datetime import date
from onegov.election_day.utils.common import LastUpdatedOrderedDict
from onegov.election_day.utils.election import get_candidates_data
from onegov.election_day.utils.election import get_candidates_results
from onegov.election_day.utils.election import get_connection_results_api
from onegov.election_day.utils.election import get_list_results
from onegov.election_day.utils.election import get_lists_data
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
        expats=False
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

    assert tuple(get_candidates_results(election, session)) == (
        (('Hegglin', 'Peter', True, 'CVP', 24132, None, None),
         ('Eder', 'Joachim', True, 'FDP', 23620, None, None),
         ('Brandenberg', 'Manuel', False, 'SVP', 10997, None, None),
         ('Gysel', 'Barbara', False, 'SP', 6612, None, None),
         ('Lustenberger', 'Andreas', False, 'ALG', 5691, None, None),
         ('Thöni', 'Stefan', False, 'Piraten', 1709, None, None))
    )

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
            'color': '#999',
            'text': 'Thöni Stefan',
            'value': 1709
        }
    ]
    assert get_candidates_data(election) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': expected,
    }
    for limit in (0, None, -3):
        assert get_candidates_data(election, limit=limit) == {
            'majority': 18191,
            'title': 'majorz_internal_staenderatswahl-2015-parties',
            'results': expected,
        }
    assert get_candidates_data(election, limit=3) == {
        'majority': 18191,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': expected[:3],
    }

    assert tuple(get_list_results(election)) == tuple()
    assert tuple(get_list_results(election, limit=0)) == tuple()
    assert tuple(get_list_results(election, limit=None)) == tuple()
    assert tuple(get_list_results(election, limit=3)) == tuple()

    assert get_lists_data(election) == {
        'majority': None,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': [],
    }
    for limit in (0, None, -3):
        assert get_lists_data(election, limit=limit) == {
            'majority': None,
            'title': 'majorz_internal_staenderatswahl-2015-parties',
            'results': [],
        }
    assert get_lists_data(election, limit=3) == {
        'majority': None,
        'title': 'majorz_internal_staenderatswahl-2015-parties',
        'results': [],
    }


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
        expats=False
    )
    assert not errors

    election.colors = {
        'CVP': '#ff6300',
        'SVP': '#3f841a',
    }

    assert tuple(get_candidates_results(election, session)) == (
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
    )

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
            'color': '#999',
            'text': 'Pezzatti Bruno',
            'value': 10174
        }
    ]
    assert get_candidates_data(election) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected,
    }
    for limit in (0, None, -3):
        assert get_candidates_data(election, limit=limit) == {
            'majority': 0,
            'title': 'proporz_internal_nationalratswahlen-2015',
            'results': expected,
        }
    assert get_candidates_data(election, limit=3) == {
        'majority': 0,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected[:3],
    }

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
    for limit in (0, None, -3):
        assert tuple(get_list_results(election, limit=limit)) == expected
    assert tuple(get_list_results(election, limit=3)) == expected[:3]

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
            'color': '#999',
            'text': 'FDP Ost',
            'value': 16285,
            'value2': 1
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'SP',
            'value': 8868,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'CVP Junge',
            'value': 6521,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'ALG',
            'value': 5844,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'SVP WuG',
            'value': 4436,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'FDP West',
            'value': 4299,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'glp',
            'value': 4178,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'SP Männer',
            'value': 3314,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'SP Frauen',
            'value': 2186,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'ALG Bildung',
            'value': 1701,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'SP Juso',
            'value': 1333,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'Piraten',
            'value': 1128,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'ALG Junge',
            'value': 807,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
            'text': 'SVP Int.',
            'value': 575,
            'value2': 0
        },
        {
            'class': 'inactive',
            'color': '#999',
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
    for limit in (0, None, -3):
        assert get_lists_data(election, limit=limit) == {
            'majority': None,
            'title': 'proporz_internal_nationalratswahlen-2015',
            'results': expected,
        }
    assert get_lists_data(election, limit=3) == {
        'majority': None,
        'title': 'proporz_internal_nationalratswahlen-2015',
        'results': expected[:3],
    }


def test_get_connection_results_interal(import_test_datasets, session):
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
# todo: test get_elected_candidates
# todo: test_election_utils_compound
