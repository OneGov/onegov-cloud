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
    upload_election_compound(client)

    for suffix in ('', '?limit=', '?limit=a', '?limit=0'):
        lists = client.get(f'/elections/elections/lists-data{suffix}')
        assert {r['text']: r['value'] for r in lists.json['results']} == {
            'FDP': 16, 'CVP': 12
        }

    lists = client.get('/elections/elections/lists-data?limit=1')
    assert {r['text']: r['value'] for r in lists.json['results']} == {
        'FDP': 16
    }


def test_view_election_compound_party_strengths(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client)
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
    assert lines[0].startswith('year,name,id,total_votes,color,mandates,votes')
    assert lines[1].startswith('2022,BDP,0,11270,#efb52c,1,60387')
    assert lines[2].startswith('2022,CVP,1,11270,#ff6300,1,49117')
    assert lines[3].startswith('2022,FDP,2,11270,#0571b0,0,35134')

    # Historical data
    csv_parties = (
        'year,name,id,total_votes,color,mandates,votes\r\n'
        '2022,BDP,0,60000,#efb52c,1,10000\r\n'
        '2022,CVP,1,60000,#ff6300,1,30000\r\n'
        '2022,FDP,2,60000,#4068c8,0,20000\r\n'
        '2018,BDP,0,40000,#efb52c,1,1000\r\n'
        '2018,CVP,1,40000,#ff6300,1,15000\r\n'
        '2018,FDP,2,40000,#4068c8,1,10000\r\n'
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

    export = client.get('/elections/elections/data-parties').text
    lines = export.split('\r\n')
    lines_csv = csv_parties.decode('utf-8').split('\r\n')
    assert all([
        line.startswith(lines_csv[index]) for index, line in enumerate(lines)
    ])


def test_view_election_compound_mandate_allocation(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client, canton='gr')
    upload_party_results(client, slug='elections/elections')

    main = client.get('/elections/elections/mandate-allocation')
    assert '<h3>Sitzzuteilung</h3>' in main

    # Historical data
    csv_parties = (
        'year,name,id,total_votes,color,mandates,votes\r\n'
        '2022,BDP,0,60000,#efb52c,1,10000\r\n'
        '2022,CVP,1,60000,#ff6300,1,30000\r\n'
        '2022,FDP,2,60000,#4068c8,0,20000\r\n'
        '2018,BDP,0,40000,#efb52c,1,1000\r\n'
        '2018,CVP,1,40000,#ff6300,1,15000\r\n'
        '2018,FDP,2,40000,#4068c8,1,10000\r\n'
    ).encode('utf-8')

    upload = client.get('/elections/elections/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    results = client.get('/elections/elections/mandate-allocation').text
    assert '2.5%' in results
    assert '16.7%' in results
    assert '14.2%' in results

    assert '37.5%' in results
    assert '50.0%' in results
    assert '12.5%' in results

    assert '25.0%' in results
    assert '33.3%' in results
    assert '8.3%' in results


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
