from datetime import date

from onegov.election_day.utils.common import LastUpdatedOrderedDict
from onegov.election_day.utils.election.connections import \
    get_connection_results_api


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


def test_get_connection_results_wabstic(import_test_datasets, session):
    election, errors = import_test_datasets(
        'wabstic',
        'election',
        'sg',
        'canton',
        election_type='proporz',
        number_of_mandates=11,
        date_=date(2019, 10, 20),
        dataset_name='NR2019-alphanumerische_list_nr',
        app_session=session
    )
    assert not errors
    results = get_connection_results_api(election, session)
    # Find the results in WPListenGde, sum for all entities
    # List conn 1 are list_id's 02a, 02b, 05
    # List conn 2 are list_id's 06a, 07, 08
    assert results['1']['total_votes'] == 88 + 27 + 49
    assert results['2']['total_votes'] == 2 + 47 + 79
    assert results['1']['subconns']['1']['total_votes'] == 88 + 27
    assert results['2']['subconns']['1']['total_votes'] == 2 + 47
