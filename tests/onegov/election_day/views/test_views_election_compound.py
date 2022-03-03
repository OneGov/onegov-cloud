from freezegun import freeze_time

from onegov.election_day.layouts import ElectionCompoundLayout
from tests.onegov.election_day.common import create_election_compound
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_election_compound
from tests.onegov.election_day.common import upload_party_results
from webtest import TestApp as Client
from webtest.forms import Upload


def test_view_election_compound_redirect(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client)

    response = client.get('/elections/elections')
    assert response.status == '302 Found'
    assert 'elections/districts' in response.headers['Location']


def test_view_election_compound_superregions(election_day_app_bl):
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, canton='bl')

    superregions = client.get('/elections/elections/superregions')
    assert 'Region 1' in superregions
    assert '0 von 5' in superregions
    assert '1 von 2' in superregions
    assert 'Region 2' in superregions
    assert '0 von 10' in superregions
    assert '1 von 3' in superregions

    assert 'Region 1' in client.get('/elections/elections/districts')
    assert 'Region 1' in client.get('/elections/elections/candidates')
    assert 'Region 1' in client.get('/elections/elections/statistics')


def test_view_election_compound_districts(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    districts = client.get('/elections/elections/districts')
    assert "Alvaschein" in districts
    assert "Belfort" in districts
    # intermediate results status_callout etc.
    assert '0 von 2' in districts        # Ausgezählt 0 von 2
    assert '0 von 15' in districts      # Mandate 0 von 15

    # Will render 0 if election is not completed
    assert "0 von 10" in districts  # Table Mandates Belfort
    assert "0 von 5" in districts  # Table Mandates Alvaschein
    assert "1 von 2" in districts  # Ausgezählt Belfort, Alvaschein


def test_view_election_compound_elected_candidates(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    candidates = client.get('/elections/elections/candidates')
    assert "Carol Winner" in candidates
    assert "Hans Sieger" in candidates
    assert "Anna Looser" not in candidates
    assert "Peter Verlierer" not in candidates
    assert "regional-election-b" in candidates
    assert "regional-election-a" in candidates
    assert "Alvaschein" in candidates
    assert "Belfort" in candidates


def test_view_election_compound_lists(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, pukelsheim=True)

    for suffix in ('', '?limit=', '?limit=a', '?limit=0'):
        lists = client.get(f'/elections/elections/lists-data{suffix}')
        assert {r['text']: r['value'] for r in lists.json['results']} == {
            'FDP': 3,  # 8 / 10 + 8 /5
            'CVP': 2   # 6 / 10 + 6 / 5
        }

    lists = client.get('/elections/elections/lists-data?limit=1')
    assert {r['text']: r['value'] for r in lists.json['results']} == {
        'FDP': 3
    }


def test_view_election_compound_party_strengths(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client, voters_counts=False)
    upload_party_results(client, slug='elections/elections')

    main = client.get('/elections/elections/party-strengths')
    assert '<h3>Parteistärken</h3>' in main

    parties = client.get('/elections/elections/party-strengths-data')
    parties = parties.json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2022']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 15
    assert parties['results']

    chart = client.get('/elections/elections/party-strengths-chart')
    assert chart.status_code == 200
    assert '/elections/elections/party-strengths-data' in chart

    export = client.get('/elections/elections/data-parties').text
    lines = export.split('\r\n')
    assert lines[0].startswith(
        'year,name,id,total_votes,total_voters_count,color,mandates,votes'
    )
    assert lines[1].startswith(
        '2022,BDP,0,11270,1445.07,#efb52c,1,60387,603.01'
    )
    assert lines[2].startswith(
        '2022,CVP,1,11270,1445.07,#ff6300,1,49117,491.02'
    )
    assert lines[3].startswith(
        '2022,FDP,2,11270,1445.07,#0571b0,0,35134,351.04'
    )

    assert client.get('/elections/elections/json').json['parties'] == {
        'BDP': {
            '2022': {
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 417, 'total': 603.01},
                'votes': {'permille': 5358, 'total': 60387}
            }
        },
        'CVP': {
            '2022': {
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 340, 'total': 491.02},
                'votes': {'permille': 4358, 'total': 49117}
            }
        },
        'FDP': {
            '2022': {
                'color': '#0571b0',
                'mandates': 0,
                'voters_count': {'permille': 243, 'total': 351.04},
                'votes': {'permille': 3117, 'total': 35134}
            }
        }
    }

    # Historical data
    csv_parties = (
        'year,name,id,total_votes,total_voters_count,color,mandates,'
        'votes,voters_count\r\n'
        '2022,BDP,0,60000,600,#efb52c,1,10000,100\r\n'
        '2022,CVP,1,60000,600,#ff6300,1,30000,300\r\n'
        '2022,FDP,2,60000,600,#4068c8,0,20000,200\r\n'
        '2018,BDP,0,40000,400,#efb52c,1,1000,10\r\n'
        '2018,CVP,1,40000,400,#ff6300,1,15000,150.7\r\n'
        '2018,FDP,2,40000,400,#4068c8,1,10000,100\r\n'
    ).encode('utf-8')

    upload = client.get('/elections/elections/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    parties = client.get('/elections/elections/party-strengths-data')
    parties = parties.json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
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
    assert parties['2018-CVP']['color'] == '#ff6300'
    assert parties['2022-CVP']['color'] == '#ff6300'
    assert parties['2018-FDP']['color'] == '#4068c8'
    assert parties['2022-FDP']['color'] == '#4068c8'

    assert parties['2018-BDP']['active'] is False
    assert parties['2018-CVP']['active'] is False
    assert parties['2018-FDP']['active'] is False
    assert parties['2022-BDP']['active'] is True
    assert parties['2022-CVP']['active'] is True
    assert parties['2022-FDP']['active'] is True

    assert parties['2018-BDP']['value']['front'] == 1
    assert parties['2018-CVP']['value']['front'] == 1
    assert parties['2018-FDP']['value']['front'] == 1
    assert parties['2022-BDP']['value']['front'] == 1
    assert parties['2022-CVP']['value']['front'] == 1
    assert parties['2022-FDP']['value']['front'] == 0

    assert parties['2018-BDP']['value']['back'] == 2.5
    assert parties['2018-CVP']['value']['back'] == 37.5
    assert parties['2018-FDP']['value']['back'] == 25
    assert parties['2022-BDP']['value']['back'] == 16.7
    assert parties['2022-CVP']['value']['back'] == 50
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
        'BDP': {
            '2018': {
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 25, 'total': 10.0},
                'votes': {'permille': 25, 'total': 1000}
            },
            '2022': {
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 167, 'total': 100.0},
                'votes': {'permille': 167, 'total': 10000}
            }
        },
        'CVP': {
            '2018': {
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 377, 'total': 150.7},
                'votes': {'permille': 375, 'total': 15000}
            },
            '2022': {
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 500, 'total': 300.0},
                'votes': {'permille': 500, 'total': 30000}
            }
        },
        'FDP': {
            '2018': {
                'color': '#4068c8',
                'mandates': 1,
                'voters_count': {'permille': 250, 'total': 100.0},
                'votes': {'permille': 250, 'total': 10000}
            },
            '2022': {
                'color': '#4068c8',
                'mandates': 0,
                'voters_count': {'permille': 333, 'total': 200.0},
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
    assert data['results'][0]['value']['back'] == 16.7
    data = client.get('/elections/elections/json').json
    assert data['parties']['CVP']['2018']['voters_count']['total'] == 150.7

    # with rounded voters counts
    edit = client.get('/elections/elections/edit')
    edit.form['exact_voters_counts'] = False
    edit.form.submit()

    assert '>10<' in client.get('/elections/elections/party-strengths')
    data = client.get('/elections/elections/party-strengths-data').json
    assert data['results'][0]['value']['back'] == 16.7
    client.get('/elections/elections/json').json['parties']
    data = client.get('/elections/elections/json').json
    assert data['parties']['CVP']['2018']['voters_count']['total'] == 151


def test_view_election_compound_list_groups(election_day_app_gr):
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

    groups = client.get('/elections/elections/list-groups-data')
    groups = groups.json
    assert groups == {
        'results': [
            {
                'class': 'inactive',
                'color': '#efb52c',
                'text': 'BDP',
                'value': 603,
                'value2': 1
            },
            {
                'class': 'inactive',
                'color': '#ff6300',
                'text': 'CVP',
                'value': 491,
                'value2': 1
            },
            {
                'class': 'inactive',
                'color': '#0571b0',
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

    groups = client.get('/elections/elections/list-groups-data')
    groups = groups.json
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
                'color': '#0571b0',
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


def test_view_election_compound_parties_panachage(election_day_app_gr):
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
        11, 12, 100, 60387 - 11 - 12 - 100,
        21, 22, 200, 49117 - 21 - 22 - 200,
        31, 32, 300, 35134 - 31 - 32 - 300
    )))


def test_view_election_compound_json(election_day_app_gr):
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
            'family_name': 'Hans',
            'first_name': 'Sieger',
            'list': 'FDP',
            'party': ''
        },
        {
            'district': 'Alvaschein',
            'family_name': 'Carol',
            'first_name': 'Winner',
            'list': 'CVP',
            'party': ''
        }
    ]
    assert data['elections']
    assert data['last_modified']
    assert data['mandates'] == {'allocated': 0, 'total': 15}
    assert data['progress'] == {'counted': 0, 'total': 2}
    assert data['title'] == {'de_CH': 'Elections'}
    assert data['type'] == 'election_compound'
    assert data['url']


def test_view_election_compound_summary(election_day_app_gr):
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


def test_view_election_compound_data(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)

    export = client.get('/elections/elections/data-json')
    assert all((expected in export for expected in ("3506", "Sieger", "153")))

    export = client.get('/elections/elections/data-csv')
    assert all((expected in export for expected in ("3506", "Sieger", "153")))


def test_views_election_compound_embedded_tables(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client)
    for tab_name in ElectionCompoundLayout.tabs_with_embedded_tables:
        client.get(f'/elections/elections/{tab_name}-table')
