from __future__ import annotations

from freezegun import freeze_time
from onegov.election_day.layouts import ElectionCompoundLayout
from tests.onegov.election_day.common import create_election_compound
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_election_compound
from tests.onegov.election_day.common import upload_party_results
from webtest import TestApp as Client
from webtest.forms import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_view_election_compound_redirect(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client)

    response = client.get('/elections/elections')
    assert response.status == '302 Found'
    assert 'elections/districts' in response.headers['Location']


def test_view_election_compound_superregions(
    election_day_app_bl: TestApp
) -> None:

    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, canton='bl')

    superregions = client.get('/elections/elections/superregions')
    assert 'Region 1' in superregions
    assert '0 von 5' in superregions
    assert '0 von 1' in superregions
    assert 'Region 2' in superregions
    assert '0 von 10' in superregions
    assert '0 von 1' in superregions

    assert 'Region 1' in client.get('/elections/elections/districts')
    assert 'Region 1' in client.get('/elections/elections/candidates')
    assert 'Region 1' in client.get('/elections/elections/statistics')

    map = client.get('/elections/elections/superregions-map')
    assert '/elections/elections/by-superregion' in map

    data = client.get('/elections/elections/by-superregion').json
    assert data == {
        'Region 1': {
            'counted': False,
            'entities': [2762, 2764, 2765, 2767, 2768, 2771, 2774, 2775],
            'link': (
                'http://localhost/elections-part/elections/'
                'superregion/region-1'
            ),
            'mandates': '0 / 5',
            'percentage': 100.0,
            'progress': '0 / 1',
            'votes': 0
        },
        'Region 2': {
            'counted': False,
            'entities': [2761, 2763, 2766, 2769, 2770, 2772, 2773, 2781, 2782,
                         2783, 2784, 2785, 2786, 2787, 2788, 2789, 2790, 2791,
                         2792, 2793],
            'link': (
                'http://localhost/elections-part/elections/'
                'superregion/region-2'
            ),
            'mandates': '0 / 10',
            'percentage': 100.0,
            'progress': '0 / 1',
            'votes': 0
        }
    }


def test_view_election_compound_districts(
    election_day_app_gr: TestApp
) -> None:

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    districts = client.get('/elections/elections/districts')
    assert "Alvaschein" in districts
    assert "Belfort" in districts
    assert '0 von 2' in districts
    assert '0 von 15' in districts
    assert "0 von 10" in districts
    assert "0 von 5" in districts
    assert "1 von 2" in districts

    map = client.get('/elections/elections/districts-map')
    assert '/elections/elections/by-district' in map

    data = client.get('/elections/elections/by-district').json
    assert data == {
        'Alvaschein': {
            'counted': False,
            'entities': [3506, 3542],
            'link': 'http://localhost/election/regional-election-a',
            'mandates': '0 / 10',
            'percentage': 100.0,
            'progress': '1 / 2',
            'votes': 0
        },
        'Belfort': {
            'counted': False,
            'entities': [3513, 3514],
            'link': 'http://localhost/election/regional-election-b',
            'mandates': '0 / 5',
            'percentage': 100.0,
            'progress': '1 / 2',
            'votes': 0
        }
    }


def test_view_election_compound_elected_candidates(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    candidates = client.get('/elections/elections/candidates')
    assert "Winner Carol" in candidates
    assert "Sieger Hans" in candidates
    assert "Looser Anna" not in candidates
    assert "Verlierer Peter" not in candidates
    assert "regional-election-b" in candidates
    assert "regional-election-a" in candidates
    assert "Alvaschein" in candidates
    assert "Belfort" in candidates


def test_view_election_compound_party_strengths(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client, voters_counts=False)
    upload_party_results(client, slug='elections/elections')

    main = client.get('/elections/elections/party-strengths')
    assert '<h3>Parteistärken</h3>' in main

    parties = client.get('/elections/elections/party-strengths-data').json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2022']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 15
    assert parties['results']

    chart = client.get('/elections/elections/party-strengths-chart')
    assert chart.status_code == 200
    assert '/elections/elections/party-strengths-data' in chart

    assert 'panel_2022' in client.get(
        '/elections/elections/party-strengths-table'
    )
    assert 'panel_2022' in client.get(
        '/elections/elections/party-strengths-table?year=2022'
    )
    assert 'panel_2022' not in client.get(
        '/elections/elections/party-strengths-table?year=2018'
    )

    export = client.get('/elections/elections/data-parties-csv').text
    lines = [l for l in export.split('\r\n') if l]
    assert lines == [
        'domain,domain_segment,year,id,'
        'name,name_de_CH,name_fr_CH,name_it_CH,name_rm_CH,'
        'total_votes,color,mandates,votes,'
        'voters_count,voters_count_percentage,panachage_votes_from_1,'
        'panachage_votes_from_2,panachage_votes_from_3,'
        'panachage_votes_from_999',
        'canton,,2022,1,BDP,BDP,,,,11270,#efb52c,'
        '1,60387,603.01,41.73,,11,12,100',
        'canton,,2022,2,CVP,CVP,,,,11270,#ff6300,'
        '1,49117,491.02,33.98,21,,22,200',
        'canton,,2022,3,FDP,FDP,,,,11270,,'
        '0,35134,351.04,24.29,31,32,,300',
    ]

    export = client.get('/elections/elections/data-parties-json').json
    assert export == [
        {
            'color': '#efb52c',
            'domain': 'canton',
            'domain_segment': None,
            'id': '1',
            'mandates': 1,
            'name': 'BDP',
            'name_de_CH': 'BDP',
            'name_fr_CH': None,
            'name_it_CH': None,
            'name_rm_CH': None,
            'panachage_votes_from_1': None,
            'panachage_votes_from_2': 11,
            'panachage_votes_from_3': 12,
            'panachage_votes_from_999': 100,
            'total_votes': 11270,
            'voters_count': 603.01,
            'voters_count_percentage': 41.73,
            'votes': 60387,
            'year': 2022
        },
        {
            'color': '#ff6300',
            'domain': 'canton',
            'domain_segment': None,
            'id': '2',
            'mandates': 1,
            'name': 'CVP',
            'name_de_CH': 'CVP',
            'name_fr_CH': None,
            'name_it_CH': None,
            'name_rm_CH': None,
            'panachage_votes_from_1': 21,
            'panachage_votes_from_2': None,
            'panachage_votes_from_3': 22,
            'panachage_votes_from_999': 200,
            'total_votes': 11270,
            'voters_count': 491.02,
            'voters_count_percentage': 33.98,
            'votes': 49117,
            'year': 2022
        },
        {
            'color': None,
            'domain': 'canton',
            'domain_segment': None,
            'id': '3',
            'mandates': 0,
            'name': 'FDP',
            'name_de_CH': 'FDP',
            'name_fr_CH': None,
            'name_it_CH': None,
            'name_rm_CH': None,
            'panachage_votes_from_1': 31,
            'panachage_votes_from_2': 32,
            'panachage_votes_from_3': None,
            'panachage_votes_from_999': 300,
            'total_votes': 11270,
            'voters_count': 351.04,
            'voters_count_percentage': 24.29,
            'votes': 35134,
            'year': 2022
        }
    ]

    assert client.get('/elections/elections/json').json['parties'] == {
        '1': {
            '2022': {
                'name': 'BDP',
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 417.3, 'total': 603.01},
                'votes': {'permille': 5358, 'total': 60387}
            }
        },
        '2': {
            '2022': {
                'name': 'CVP',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 339.8, 'total': 491.02},
                'votes': {'permille': 4358, 'total': 49117}
            }
        },
        '3': {
            '2022': {
                'name': 'FDP',
                'color': None,
                'mandates': 0,
                'voters_count': {'permille': 242.9, 'total': 351.04},
                'votes': {'permille': 3117, 'total': 35134}
            }
        }
    }

    # Historical data with translations
    csv_parties = (
        'year,name,name_fr_ch,id,total_votes,color,mandates,'
        'votes,voters_count,voters_count_percentage\r\n'
        '2022,BDP,,1,60000,#efb52c,1,10000,100,16.67\r\n'
        '2022,Die Mitte,Le Centre,2,60000,#ff6300,1,30000,300,50\r\n'
        '2022,FDP,,3,60000,#4068c8,0,20000,200,33.33\r\n'
        '2018,BDP,,1,40000,#efb52c,1,1000,10,2.5\r\n'
        '2018,CVP,PDC,2,40000,#ff6300,1,15000,150.7,37.67\r\n'
        '2018,FDP,,3,40000,#4068c8,1,10000,100,25.0\r\n'
    ).encode('utf-8')

    upload = client.get('/elections/elections/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    parties = client.get('/elections/elections/party-strengths-data').json
    assert parties['groups'] == ['BDP', 'Die Mitte', 'FDP']
    assert parties['labels'] == ['2018', '2022']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 15
    assert parties['results']

    parties = {
        '{}-{}'.format(party['item'], party['group']): party
        for party in parties['results']
    }
    assert parties['2018-BDP']['color'] == '#efb52c'
    assert parties['2022-BDP']['color'] == '#efb52c'
    assert parties['2018-Die Mitte']['color'] == '#ff6300'
    assert parties['2022-Die Mitte']['color'] == '#ff6300'
    assert parties['2018-FDP']['color'] == '#4068c8'
    assert parties['2022-FDP']['color'] == '#4068c8'

    assert parties['2018-BDP']['active'] is False
    assert parties['2018-Die Mitte']['active'] is False
    assert parties['2018-FDP']['active'] is False
    assert parties['2022-BDP']['active'] is True
    assert parties['2022-Die Mitte']['active'] is True
    assert parties['2022-FDP']['active'] is True

    assert parties['2018-BDP']['value']['front'] == 1
    assert parties['2018-Die Mitte']['value']['front'] == 1
    assert parties['2018-FDP']['value']['front'] == 1
    assert parties['2022-BDP']['value']['front'] == 1
    assert parties['2022-Die Mitte']['value']['front'] == 1
    assert parties['2022-FDP']['value']['front'] == 0

    assert parties['2018-BDP']['value']['back'] == 2.5
    assert parties['2018-Die Mitte']['value']['back'] == 37.5
    assert parties['2018-FDP']['value']['back'] == 25
    assert parties['2022-BDP']['value']['back'] == 16.7
    assert parties['2022-Die Mitte']['value']['back'] == 50
    assert parties['2022-FDP']['value']['back'] == 33.3

    results = client.get('/elections/elections/party-strengths').text
    assert '2.5%' in results
    assert '16.7%' in results
    assert '14.2%' in results

    assert '37.5%' in results
    assert '50.0%' in results
    assert '12.5%' in results

    assert '25.0%' in results
    assert '33.3%' in results
    assert '8.3%' in results

    assert client.get('/elections/elections/json').json['parties'] == {
        '1': {
            '2018': {
                'name': 'BDP',
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 25.0, 'total': 10.0},
                'votes': {'permille': 25, 'total': 1000}
            },
            '2022': {
                'name': 'BDP',
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 166.7, 'total': 100.0},
                'votes': {'permille': 167, 'total': 10000}
            }
        },
        '2': {
            '2018': {
                'name': 'CVP',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 376.7, 'total': 150.7},
                'votes': {'permille': 375, 'total': 15000}
            },
            '2022': {
                'name': 'Die Mitte',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 500.0, 'total': 300.0},
                'votes': {'permille': 500, 'total': 30000}
            }
        },
        '3': {
            '2018': {
                'name': 'FDP',
                'color': '#4068c8',
                'mandates': 1,
                'voters_count': {'permille': 250.0, 'total': 100.0},
                'votes': {'permille': 250, 'total': 10000}
            },
            '2022': {
                'name': 'FDP',
                'color': '#4068c8',
                'mandates': 0,
                'voters_count': {'permille': 333.3, 'total': 200.0},
                'votes': {'permille': 333, 'total': 20000}
            }
        }
    }

    # with exact voters counts
    edit = client.get('/elections/elections/edit')
    edit.form['voters_counts'] = True
    edit.form.submit()

    assert '>10.00<' in client.get('/elections/elections/party-strengths')
    data = client.get('/elections/elections/party-strengths-data').json
    assert data['results'][0]['value']['back'] == 16.67
    data = client.get('/elections/elections/json').json
    assert data['parties']['2']['2018']['voters_count']['total'] == 150.7

    # with rounded voters counts
    edit = client.get('/elections/elections/edit')
    edit.form['exact_voters_counts'] = False
    edit.form.submit()

    assert '>10<' in client.get('/elections/elections/party-strengths')
    data = client.get('/elections/elections/party-strengths-data').json
    assert data['results'][0]['value']['back'] == 16.67
    data = client.get('/elections/elections/json').json
    assert data['parties']['2']['2018']['voters_count']['total'] == 151

    # translations
    client.get('/locale/fr_CH')
    parties = client.get('/elections/elections/party-strengths-data')
    parties = parties.json
    assert parties['groups'] == ['BDP', 'Le Centre', 'FDP']
    results = client.get('/elections/elections/party-strengths').text
    assert 'Le Centre' in results
    assert 'PDC' in results
    assert 'BDP' in results

    # with horizontal_party_strengths
    data = client.get(
        '/elections/elections/party-strengths-data?horizontal=1'
    ).json
    assert data['results'][0]['text'] == 'Le Centre 2022'
    assert data['results'][0]['value'] == 50.0
    assert data['results'][0]['percentage'] == True


def test_view_election_compound_seat_allocation(
    election_day_app_gr: TestApp
) -> None:

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client, voters_counts=False)
    upload_party_results(client, slug='elections/elections')

    main = client.get('/elections/elections/seat-allocation')
    assert '<h3>Sitzverteilung</h3>' in main

    parties = client.get('/elections/elections/seat-allocation-data').json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2022']
    assert parties['maximum']['front'] == 15
    assert parties['results']

    chart = client.get('/elections/elections/seat-allocation-chart')
    assert chart.status_code == 200
    assert '/elections/elections/seat-allocation-data' in chart

    # Historical data with translations
    csv_parties = (
        'year,name,name_fr_ch,id,color,mandates,\r\n'
        '2022,BDP,,1,#efb52c,0\r\n'
        '2022,Die Mitte,Le Centre,2,#ff6300,1\r\n'
        '2022,FDP,,3,#4068c8,2\r\n'
        '2018,BDP,,1,#efb52c,3\r\n'
        '2018,CVP,PDC,2,#ff6300,4\r\n'
        '2018,FDP,,3,#4068c8,5\r\n'
    ).encode('utf-8')

    upload = client.get('/elections/elections/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    parties = client.get('/elections/elections/seat-allocation-data').json
    assert parties['groups'] == ['BDP', 'Die Mitte', 'FDP']
    assert parties['labels'] == ['2018', '2022']
    assert parties['maximum']['front'] == 15
    assert parties['results']

    parties = {
        '{}-{}'.format(party['item'], party['group']): party
        for party in parties['results']
    }
    assert parties['2018-BDP']['color'] == '#efb52c'
    assert parties['2022-BDP']['color'] == '#efb52c'
    assert parties['2018-Die Mitte']['color'] == '#ff6300'
    assert parties['2022-Die Mitte']['color'] == '#ff6300'
    assert parties['2018-FDP']['color'] == '#4068c8'
    assert parties['2022-FDP']['color'] == '#4068c8'

    assert parties['2018-BDP']['active'] is False
    assert parties['2018-Die Mitte']['active'] is False
    assert parties['2018-FDP']['active'] is False
    assert parties['2022-BDP']['active'] is True
    assert parties['2022-Die Mitte']['active'] is True
    assert parties['2022-FDP']['active'] is True

    assert parties['2018-BDP']['value']['front'] == 3
    assert parties['2018-Die Mitte']['value']['front'] == 4
    assert parties['2018-FDP']['value']['front'] == 5
    assert parties['2022-BDP']['value']['front'] == 0
    assert parties['2022-Die Mitte']['value']['front'] == 1
    assert parties['2022-FDP']['value']['front'] == 2

    results = client.get('/elections/elections/seat-allocation').text
    assert '>0<' in results
    assert '>1<' in results
    assert '>2<' in results
    assert '>3<' in results
    assert '>4<' in results
    assert '>5<' in results

    # translations
    client.get('/locale/fr_CH')
    parties = client.get('/elections/elections/seat-allocation-data').json
    assert parties['groups'] == ['BDP', 'Le Centre', 'FDP']
    results = client.get('/elections/elections/seat-allocation').text
    assert 'Le Centre' in results
    assert 'BDP' in results


def test_view_election_compound_list_groups(
    election_day_app_gr: TestApp
) -> None:

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(
        client, pukelsheim=True, completes_manually=True, status='final'
    )
    upload_party_results(client, slug='elections/elections')

    # intermediate results
    main = client.get('/elections/elections/list-groups')
    assert '<h3>Listengruppen</h3>' in main
    assert 'BDP' in main
    assert 'data-text="603.01"' in main

    groups = client.get('/elections/elections/list-groups-data').json
    assert groups == {
        'results': [
            {
                'class': 'active',
                'color': '#efb52c',
                'text': 'BDP',
                'value': 603,
                'value2': 1
            },
            {
                'class': 'active',
                'color': '#ff6300',
                'text': 'CVP',
                'value': 491,
                'value2': 1
            },
            {
                'class': 'active',  # no mandates allocated yet
                'color': None,
                'text': 'FDP',
                'value': 351,
                'value2': 0
            }
        ]
    }

    chart = client.get('/elections/elections/list-groups-chart')
    assert chart.status_code == 200
    assert '/elections/elections/list-groups-data' in chart

    # final results
    edit = client.get('/elections/elections/edit')
    edit.form['manually_completed'] = True
    edit.form.submit()

    main = client.get('/elections/elections/list-groups')
    assert '<h3>Listengruppen</h3>' in main
    assert 'BDP' in main

    groups = client.get('/elections/elections/list-groups-data').json
    assert groups == {
        'results': [
            {
                'class': 'active',
                'color': '#efb52c',
                'text': 'BDP',
                'value': 603,
                'value2': 1
            },
            {
                'class': 'active',
                'color': '#ff6300',
                'text': 'CVP',
                'value': 491,
                'value2': 1
            },
            {
                'class': 'inactive',
                'color': None,
                'text': 'FDP',
                'value': 351,
                'value2': 0
            }
        ]
    }

    # with rounded voters counts
    edit = client.get('/elections/elections/edit')
    edit.form['exact_voters_counts'] = False
    edit.form.submit()
    main = client.get('/elections/elections/list-groups')
    assert 'data-text="603"' in main


def test_view_election_compound_parties_panachage(
    election_day_app_gr: TestApp
) -> None:

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client)
    upload_party_results(client, slug='elections/elections')

    main = client.get('/elections/elections/parties-panachage')
    assert '<h3>Panaschierstatistik</h3>' in main

    data = client.get('/elections/elections/parties-panachage-data').json

    nodes = [node['name'] for node in data['nodes']]
    assert 'Blankoliste' in nodes
    assert 'BDP' in nodes
    assert 'CVP' in nodes
    assert 'FDP' in nodes

    colors = [node['color'] for node in data['nodes']]
    assert '#efb52c' in colors
    assert '#ff6300' in colors

    links = [link['value'] for link in data['links']]
    assert all((i in links for i in (
        11, 12, 100,
        21, 22, 200,
        31, 32, 300,
    )))

    chart = client.get('/elections/elections/parties-panachage-chart')
    assert 'elections/elections/parties-panachage-data' in chart


def test_view_election_compound_statistics(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    statistics = client.get('/elections/elections/statistics')
    assert "Alvaschein" in statistics
    assert "Belfort" in statistics
    assert "Noch nicht ausgezählt" in statistics

    assert "Gewählte Kandidierende" in statistics
    assert "weiblich"
    assert ">37<" in statistics


def test_view_election_compound_json(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    response = client.get('/elections/elections/json')
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    data = response.json
    assert data['completed'] == False
    assert data['data']['csv']
    assert data['data']['json']
    assert data['date'] == '2022-01-01'
    assert data['districts'] == [
        {
            'mandates': {'allocated': 0, 'total': 10},
            'name': 'Alvaschein',
            'progress': {'counted': 1, 'total': 2}
        },
        {
            'mandates': {'allocated': 0, 'total': 5},
            'name': 'Belfort',
            'progress': {'counted': 1, 'total': 2}
        }
    ]
    assert data['elected_candidates'] == [
        {
            'district': 'Belfort',
            'family_name': 'Sieger',
            'first_name': 'Hans',
            'list': 'FDP',
            'party': ''
        },
        {
            'district': 'Alvaschein',
            'family_name': 'Winner',
            'first_name': 'Carol',
            'list': 'CVP',
            'party': ''
        }
    ]
    assert data['candidate_statistics'] == {
        'female': {'age': 32, 'count': 1},
        'male': {'age': 42, 'count': 1},
        'total': {'age': 37, 'count': 2}
    }

    assert data['elections']
    assert data['last_modified']
    assert data['mandates'] == {'allocated': 0, 'total': 15}
    assert data['progress'] == {'counted': 0, 'total': 2}
    assert data['title'] == {'de_CH': 'Elections'}
    assert data['type'] == 'election_compound'
    assert data['url']


def test_view_election_compound_summary(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2022-01-01 12:00"):
        upload_election_compound(client)

        response = client.get('/elections/elections/summary')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'completed': False,
            'date': '2022-01-01',
            'domain': 'canton',
            'elected': [['Carol', 'Winner'], ['Hans', 'Sieger']],
            'elections': [
                'http://localhost/election/regional-election-a',
                'http://localhost/election/regional-election-b'
            ],
            'last_modified': '2022-01-01T12:00:00+00:00',
            'progress': {'counted': 0, 'total': 2},
            'title': {'de_CH': 'Elections'},
            'type': 'election_compound',
            'url': 'http://localhost/elections/elections'
        }


def test_view_election_compound_data(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    main = client.get('/elections/elections/data')
    assert '/elections/elections/data-json' in main
    assert '/elections/elections/data-csv' in main

    data = client.get('/elections/elections/data-json')
    assert data.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert data.headers['Content-Disposition'] == (
        'inline; filename=elections.json')
    assert all((expected in data for expected in ("3506", "Sieger", "153")))

    data = client.get('/elections/elections/data-csv')
    assert data.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert data.headers['Content-Disposition'] == (
        'inline; filename=elections.csv')
    assert all((expected in data for expected in ("3506", "Sieger", "153")))


def test_view_election_compound_relations(
    election_day_app_zg: TestApp
) -> None:

    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'Election'
    new.form['date'] = '2022-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form.submit()

    new = client.get('/manage/election-compounds/new-election-compound')
    new.form['title_de'] = 'First Compound'
    new.form['date'] = '2022-01-01'
    new.form['municipality_elections'] = ['election']
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'municipality'
    new.form.submit()

    new = client.get('/manage/election-compounds/new-election-compound')
    new.form['title_de'] = 'Second Compound'
    new.form['date'] = '2022-01-01'
    new.form['municipality_elections'] = ['election']
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'municipality'
    new.form['related_compounds_historical'] = ['first-compound']
    new.form['related_compounds_other'] = ['first-compound']
    new.form.submit()

    upload_party_results(client, 'elections/first-compound')
    upload_party_results(client, 'elections/second-compound')

    for page in ('candidates', 'statistics', 'data'):
        result = client.get(f'/elections/first-compound/{page}')
        assert '<h2>Zugehörige Wahlen</h2>' in result
        assert 'http://localhost/elections/second-compound' in result
        assert 'Second Compound' in result

        result = client.get(f'/elections/second-compound/{page}')
        assert '<h2>Zugehörige Wahlen</h2>' in result
        assert 'http://localhost/elections/first-compound' in result
        assert 'First Compound' in result


def test_views_election_compound_embedded_tables(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)
    for tab_name in ElectionCompoundLayout.tabs_with_embedded_tables:
        client.get(f'/elections/elections/{tab_name}-table')
