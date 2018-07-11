from freezegun import freeze_time
from onegov.election_day.tests.common import create_election_compound
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import upload_election_compound
from onegov.election_day.tests.common import upload_party_results
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
    assert "Regional Election A" in districts
    assert "Regional Election B" in districts
    assert "1 von 10" in districts  # mandates A
    assert "1 von 5" in districts  # mandates B
    assert "2 von 15" in districts  # overall mandates
    assert "1 von 10" in districts  # municipalites A
    assert "1 von 24" in districts  # municipalites B
    assert "0 von 2" in districts  # overall counted


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
    assert "Albula" in candidates
    assert "Hinterrhein" in candidates


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
    assert parties['labels'] == ['2015']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 15
    assert parties['results']

    chart = client.get('/elections/elections/party-strengths-chart')
    assert chart.status_code == 200
    assert '/elections/elections/party-strengths-data' in chart

    export = client.get('/elections/elections/data-parties').text
    lines = export.split('\r\n')
    assert lines[0].startswith('year,name,id,total_votes,color,mandates,votes')
    assert lines[1].startswith('2015,BDP,0,11270,#efb52c,1,60387')
    assert lines[2].startswith('2015,CVP,1,11270,#ff6300,1,49117')
    assert lines[3].startswith('2015,FDP,2,11270,#0571b0,0,35134')

    # Historical data
    csv_parties = (
        'year,name,id,total_votes,color,mandates,votes\r\n'
        '2015,BDP,0,60000,#efb52c,1,10000\r\n'
        '2015,CVP,1,60000,#ff6300,1,30000\r\n'
        '2015,FDP,2,60000,#4068c8,0,20000\r\n'
        '2011,BDP,0,40000,#efb52c,1,1000\r\n'
        '2011,CVP,1,40000,#ff6300,1,15000\r\n'
        '2011,FDP,2,40000,#4068c8,1,10000\r\n'
    ).encode('utf-8')

    upload = client.get('/elections/elections/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    parties = client.get('/elections/elections/party-strengths-data')
    parties = parties.json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2011', '2015']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 15
    assert parties['results']

    parties = {
        '{}-{}'.format(party['item'], party['group']): party
        for party in parties['results']
    }
    assert parties['2011-BDP']['color'] == '#efb52c'
    assert parties['2015-BDP']['color'] == '#efb52c'
    assert parties['2011-CVP']['color'] == '#ff6300'
    assert parties['2015-CVP']['color'] == '#ff6300'
    assert parties['2011-FDP']['color'] == '#4068c8'
    assert parties['2015-FDP']['color'] == '#4068c8'

    assert parties['2011-BDP']['active'] is False
    assert parties['2011-CVP']['active'] is False
    assert parties['2011-FDP']['active'] is False
    assert parties['2015-BDP']['active'] is True
    assert parties['2015-CVP']['active'] is True
    assert parties['2015-FDP']['active'] is True

    assert parties['2011-BDP']['value']['front'] == 1
    assert parties['2011-CVP']['value']['front'] == 1
    assert parties['2011-FDP']['value']['front'] == 1
    assert parties['2015-BDP']['value']['front'] == 1
    assert parties['2015-CVP']['value']['front'] == 1
    assert parties['2015-FDP']['value']['front'] == 0

    assert parties['2011-BDP']['value']['back'] == 2.5
    assert parties['2011-CVP']['value']['back'] == 37.5
    assert parties['2011-FDP']['value']['back'] == 25
    assert parties['2015-BDP']['value']['back'] == 16.7
    assert parties['2015-CVP']['value']['back'] == 50
    assert parties['2015-FDP']['value']['back'] == 33.3

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
    assert all((expected in str(response.json) for expected in (
        "Carol", "Winner", "Hans", "Sieger"
    )))


def test_view_election_compound_summary(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2014-01-01 12:00"):
        upload_election_compound(client)

        response = client.get('/elections/elections/summary')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'completed': False,
            'date': '2015-01-01',
            'domain': 'canton',
            'elections': [
                'http://localhost/election/regional-election-a',
                'http://localhost/election/regional-election-b'
            ],
            'last_modified': '2014-01-01T12:00:00+00:00',
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
    assert all((expected in export for expected in ("3503", "Sieger", "153")))

    export = client.get('/elections/elections/data-csv')
    assert all((expected in export for expected in ("3503", "Sieger", "153")))
