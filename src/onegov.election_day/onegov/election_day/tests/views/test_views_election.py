from datetime import date
from freezegun import freeze_time
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import MAJORZ_HEADER
from onegov.election_day.tests.common import upload_majorz_election
from onegov.election_day.tests.common import upload_party_results
from onegov.election_day.tests.common import upload_proporz_election
from webtest import TestApp as Client
from webtest.forms import Upload


def test_view_election_redirect(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_majorz_election(client)
    upload_proporz_election(client)

    response = client.get('/election/majorz-election')
    assert response.status == '302 Found'
    assert 'majorz-election/candidates' in response.headers['Location']

    response = client.get('/election/proporz-election')
    assert response.status == '302 Found'
    assert 'proporz-election/lists' in response.headers['Location']


def test_view_election_candidates(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    candidates = client.get('/election/majorz-election/candidates')
    assert all((expected in candidates for expected in (
        "Engler Stefan", "20", "Schmid Martin", "18"
    )))

    chart = client.get('/election/majorz-election/candidates-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/candidates' in chart

    candidates = client.get('/election/proporz-election/candidates')
    assert all((expected in candidates for expected in (
        "Caluori Corina", "1", "Casanova Angela", "0"
    )))

    chart = client.get('/election/proporz-election/candidates-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/candidates' in chart


def test_view_election_candidate_by_entity(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    for url in (
        '/election/majorz-election/candidate-by-entity',
        '/election/majorz-election/candidate-by-entity-chart'
    ):
        view = client.get(url)
        assert '/by-entity">Engler Stefan (gewählt)</option>' in view
        assert '/by-entity">Schmid Martin (gewählt)</option>' in view

        data = {
            option.text.split(' ')[0]: client.get(option.attrib['value']).json
            for option in view.pyquery('option')
        }
        assert data['Engler']['3503']['counted'] == True
        assert data['Engler']['3503']['percentage'] == 100 * 20 / 41
        assert data['Schmid']['3503']['counted'] == True
        assert data['Schmid']['3503']['percentage'] == 100 * 18 / 41

    for url in (
        '/election/proporz-election/candidate-by-entity',
        '/election/proporz-election/candidate-by-entity-chart'
    ):
        view = client.get(url)
        assert '/by-entity">Caluori Corina</option>' in view
        assert '/by-entity">Casanova Angela</option' in view

        data = {
            option.text.split(' ')[0]: client.get(option.attrib['value']).json
            for option in view.pyquery('option')
        }
        assert data['Caluori']['3503']['counted'] == True
        assert data['Caluori']['3503']['percentage'] == 100 * 2 / 153
        assert data['Casanova']['3503']['counted'] == True
        assert data['Casanova']['3503']['percentage'] == 0.0


def test_view_election_candidate_by_district(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    for url in (
        '/election/majorz-election/candidate-by-district',
        '/election/majorz-election/candidate-by-district-chart'
    ):
        view = client.get(url)
        assert '/by-district">Engler Stefan (gewählt)</option>' in view
        assert '/by-district">Schmid Martin (gewählt)</option>' in view

        data = {
            option.text.split(' ')[0]: client.get(option.attrib['value']).json
            for option in view.pyquery('option')
        }
        assert data['Engler']['Bernina']['entities'] == [3551, 3561]
        assert data['Engler']['Bernina']['counted'] == False
        assert data['Engler']['Bernina']['percentage'] == 0.0
        assert data['Schmid']['Bernina']['entities'] == [3551, 3561]
        assert data['Schmid']['Bernina']['counted'] == False
        assert data['Schmid']['Bernina']['percentage'] == 0.0

    for url in (
        '/election/proporz-election/candidate-by-district',
        '/election/proporz-election/candidate-by-district-chart'
    ):
        view = client.get(url)
        assert '/by-district">Caluori Corina</option>' in view
        assert '/by-district">Casanova Angela</option' in view

        data = {
            option.text.split(' ')[0]: client.get(option.attrib['value']).json
            for option in view.pyquery('option')
        }
        assert data['Caluori']['Bernina']['entities'] == [3551, 3561]
        assert data['Caluori']['Bernina']['counted'] == False
        assert data['Caluori']['Bernina']['percentage'] == 0.0
        assert data['Casanova']['Bernina']['entities'] == [3551, 3561]
        assert data['Casanova']['Bernina']['counted'] == False
        assert data['Casanova']['Bernina']['percentage'] == 0.0


def test_view_election_statistics(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    statistics = client.get('/election/majorz-election/statistics')
    assert all((expected in statistics for expected in (
        "1 von 125", "Grüsch", "56", "25", "21", "41", "Noch nicht ausgezählt"
    )))

    statistics = client.get('/election/proporz-election/statistics')
    assert all((expected in statistics for expected in (
        "1 von 125", "Grüsch", "56", "32", "31", "153", "Noch nicht ausgezählt"
    )))


def test_view_election_lists(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/lists')
    assert '<h3>Listen</h3>' not in main

    lists = client.get('/election/majorz-election/lists-data')
    assert lists.json['results'] == []

    chart = client.get('/election/majorz-election/lists-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/lists' in chart

    upload_proporz_election(client)

    main = client.get('/election/proporz-election/lists')
    assert '<h3>Listen</h3>' in main

    lists = client.get('/election/proporz-election/lists-data')
    assert all((expected in lists for expected in ("FDP", "8", "CVP", "6")))

    chart = client.get('/election/proporz-election/lists-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/lists-data' in chart


def test_view_election_list_by_entity(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    url = '/election/majorz-election'
    assert '</option>' not in client.get(f'{url}/list-by-entity')
    assert '</option>' not in client.get(f'{url}/list-by-entity-chart')

    for url in (
        '/election/proporz-election/list-by-entity',
        '/election/proporz-election/list-by-entity-chart'
    ):
        view = client.get(url)
        assert '/by-entity">CVP</option>' in view
        assert '/by-entity">FDP</option' in view

        data = {
            option.text: client.get(option.attrib['value']).json
            for option in view.pyquery('option')
        }
        assert data['CVP']['3503']['counted'] == True
        assert data['CVP']['3503']['percentage'] == 100 * 6 / 153
        assert data['FDP']['3503']['counted'] == True
        assert data['FDP']['3503']['percentage'] == 100 * 8 / 153


def test_view_election_list_by_district(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    url = '/election/majorz-election'
    assert '</option>' not in client.get(f'{url}/list-by-district')
    assert '</option>' not in client.get(f'{url}/list-by-district-chart')

    for url in (
        '/election/proporz-election/list-by-district',
        '/election/proporz-election/list-by-district-chart'
    ):
        view = client.get(url)
        assert '/by-district">CVP</option>' in view
        assert '/by-district">FDP</option' in view

        data = {
            option.text: client.get(option.attrib['value']).json
            for option in view.pyquery('option')
        }
        assert data['CVP']['Bernina']['entities'] == [3551, 3561]
        assert data['CVP']['Bernina']['counted'] == False
        assert data['CVP']['Bernina']['percentage'] == 0.0
        assert data['FDP']['Bernina']['entities'] == [3551, 3561]
        assert data['FDP']['Bernina']['counted'] == False
        assert data['FDP']['Bernina']['percentage'] == 0.0


def test_view_election_party_strengths(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()
    login(client)

    # Majorz election
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/party-strengths')
    assert '<h4>Parteistärken</h4>' not in main

    parties = client.get('/election/majorz-election/party-strengths-data')
    assert parties.json['results'] == []

    chart = client.get('/election/majorz-election/party-strengths-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/party-strengths' in chart

    # Proporz election
    upload_proporz_election(client)
    upload_party_results(client)

    main = client.get('/election/proporz-election/party-strengths')
    assert '<h4>Parteistärken</h4>' in main

    parties = client.get('/election/proporz-election/party-strengths-data')
    parties = parties.json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2015']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 5
    assert parties['results']

    chart = client.get('/election/proporz-election/party-strengths-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/party-strengths-data' in chart

    export = client.get('/election/proporz-election/data-parties').text
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

    upload = client.get('/election/proporz-election/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    parties = client.get('/election/proporz-election/party-strengths-data')
    parties = parties.json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2011', '2015']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 5
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

    results = client.get('/election/proporz-election/party-strengths').text
    assert '2.5%' in results
    assert '16.7%' in results
    assert '14.2%' in results

    assert '37.5%' in results
    assert '50.0%' in results
    assert '12.5%' in results

    assert '25.0%' in results
    assert '33.3%' in results
    assert '8.3%' in results

    export = client.get('/election/proporz-election/data-parties').text
    lines = export.split('\r\n')
    lines_csv = csv_parties.decode('utf-8').split('\r\n')
    assert all([
        line.startswith(lines_csv[index]) for index, line in enumerate(lines)
    ])


def test_view_election_connections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/connections')
    assert '<h4>Listenverbindungen</h4>' not in main

    assert client.get('/election/majorz-election/connections-data').json == {}

    chart = client.get('/election/majorz-election/connections-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/connections-data' in chart

    upload_proporz_election(client)

    main = client.get('/election/proporz-election/connections')
    assert '<h4>Listenverbindungen</h4>' in main

    data = client.get('/election/proporz-election/connections-data').json

    nodes = [node['name'] for node in data['nodes']]
    assert 'FDP' in nodes
    assert 'CVP' in nodes

    links = [
        '{}:{}'.format(link['source'], link['value']) for link in data['links']
    ]
    assert '{}:8'.format(nodes.index('FDP')) in links
    assert '{}:6'.format(nodes.index('CVP')) in links

    chart = client.get('/election/proporz-election/connections-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/connections-data' in chart


def test_view_election_lists_panachage(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/lists-panachage')
    assert '<h4>Panaschierstatistik</h4>' not in main

    assert client.get(
        '/election/majorz-election/lists-panachage-data'
    ).json == {}

    chart = client.get('/election/majorz-election/lists-panachage-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/lists-panachage-data' in chart

    upload_proporz_election(client)

    main = client.get('/election/proporz-election/lists-panachage')
    assert '<h4>Panaschierstatistik</h4>' in main

    data = client.get('/election/proporz-election/lists-panachage-data').json

    nodes = [node['name'] for node in data['nodes']]
    assert 'Blankoliste' in nodes
    assert 'FDP' in nodes
    assert 'CVP' in nodes

    links = [link['value'] for link in data['links']]
    assert all((i in links for i in (1, 2, 4, 7)))


def test_view_election_parties_panachage(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/parties-panachage')
    assert '<h4>Panaschierstatistik</h4>' not in main

    assert client.get(
        '/election/majorz-election/parties-panachage-data'
    ).json == {}

    chart = client.get('/election/majorz-election/parties-panachage-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/parties-panachage-data' in chart

    upload_proporz_election(client)
    upload_party_results(client)

    main = client.get('/election/proporz-election/parties-panachage')
    assert '<h4>Panaschierstatistik</h4>' in main

    data = client.get('/election/proporz-election/parties-panachage-data').json

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


def test_view_election_json(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    response = client.get('/election/majorz-election/json')
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    assert all((expected in str(response.json) for expected in (
        "Engler", "Stefan", "20", "Schmid", "Martin", "18"
    )))

    response = client.get('/election/proporz-election/json')
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    assert all((expected in str(response.json) for expected in (
        "Casanova", "Angela", "56", "Caluori", "Corina", "32", "CVP", "FDP"
    )))


def test_view_election_summary(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2014-01-01 12:00"):
        upload_majorz_election(client)
        upload_proporz_election(client)

        response = client.get('/election/majorz-election/summary')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'completed': False,
            'date': '2015-01-01',
            'domain': 'federation',
            'elected': [['Stefan', 'Engler'], ['Martin', 'Schmid']],
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 1, 'total': 125},
            'title': {'de_CH': 'Majorz Election'},
            'type': 'election',
            'url': 'http://localhost/election/majorz-election',
        }

        response = client.get('/election/proporz-election/summary')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'completed': False,
            'date': '2015-01-01',
            'domain': 'federation',
            'elected': [],
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 1, 'total': 125},
            'title': {'de_CH': 'Proporz Election'},
            'type': 'election',
            'url': 'http://localhost/election/proporz-election',
        }


def test_view_election_data(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    export = client.get('/election/majorz-election/data-json')
    assert all((expected in export for expected in ("3503", "Engler", "20")))

    export = client.get('/election/majorz-election/data-csv')
    assert all((expected in export for expected in ("3503", "Engler", "20")))

    export = client.get('/election/proporz-election/data-json')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))

    export = client.get('/election/proporz-election/data-csv')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))


def test_view_election_tacit(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Tacit Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 2
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['tacit'] = True
    new.form.submit()

    csv = MAJORZ_HEADER
    csv += (
        "final,,3503,True,56,0,0,0,0,0,1,True,Engler,Stefan,0,\n"
        "final,,3503,True,56,0,0,0,0,0,2,True,Schmid,Martin,0,\n"
    )
    csv = csv.encode('utf-8')

    upload = client.get('/election/tacit-election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()
    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    candidates = client.get('/election/tacit-election/candidates')
    assert "Engler Stefan" in candidates
    assert "Schmid Martin" in candidates
    assert "Wahlbeteiligung" not in candidates


def test_view_election_relations(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'First Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 2
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Second Election'
    new.form['date'] = date(2015, 1, 2)
    new.form['mandates'] = 2
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['related_elections'] = 'first-election'
    new.form.submit()

    csv = MAJORZ_HEADER
    csv += (
        "final,,3503,True,56,0,0,0,0,0,1,True,Engler,Stefan,0,\n"
        "final,,3503,True,56,0,0,0,0,0,2,True,Schmid,Martin,0,\n"
    )
    csv = csv.encode('utf-8')

    for count in ('first', 'second'):
        upload = client.get(f'/election/{count}-election/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()
        assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    for page in ('candidates', 'statistics', 'data'):
        result = client.get(f'/election/first-election/{page}')
        assert '<h2>Zugehörige Wahlen</h2>' in result
        assert 'http://localhost/election/second-election' in result
        assert 'Second Election' in result

        result = client.get(f'/election/second-election/{page}')
        assert '<h2>Zugehörige Wahlen</h2>' in result
        assert 'http://localhost/election/first-election' in result
        assert 'First Election' in result
