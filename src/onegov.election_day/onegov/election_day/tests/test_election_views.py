from freezegun import freeze_time
from webtest import TestApp as Client
from onegov.election_day.tests import login
from onegov.election_day.tests import upload_majorz_election
from onegov.election_day.tests import upload_proporz_election


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


def test_view_election_districts(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    districts = client.get('/election/majorz-election/districts')
    assert all((expected in districts for expected in (
        "Engler Stefan", "20", "Schmid Martin", "18", "Grüsch"
    )))

    districts = client.get('/election/proporz-election/districts')
    assert not any((expected in districts for expected in (
        "Caluori Corina", "Casanova Angela"
    )))


def test_view_election_statistics(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    statistics = client.get('/election/majorz-election/statistics')
    assert all((expected in statistics for expected in (
        "Grüsch", "56", "25", "21", "41"
    )))

    statistics = client.get('/election/proporz-election/statistics')
    assert all((expected in statistics for expected in (
        "Grüsch", "56", "32", "31", "154"
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
    assert all((expected in lists for expected in ("FDP", "8", "CVP", "5")))

    chart = client.get('/election/proporz-election/lists-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/lists-data' in chart


def test_view_election_parties(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/parties')
    assert '<h3>Parteien</h3>' not in main

    parties = client.get('/election/majorz-election/parties-data')
    assert parties.json['results'] == []

    chart = client.get('/election/majorz-election/parties-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/parties' in chart

    upload_proporz_election(client)

    main = client.get('/election/proporz-election/parties')
    assert '<h3>Parteien</h3>' in main

    parties = client.get('/election/proporz-election/parties-data').json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2015']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 5
    assert parties['results']

    chart = client.get('/election/proporz-election/parties-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/parties-data' in chart


def test_view_election_connections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/connections')
    assert '<h3>Listenverbindungen</h3>' not in main

    assert client.get('/election/majorz-election/connections-data').json == {}

    chart = client.get('/election/majorz-election/connections-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/connections-data' in chart

    upload_proporz_election(client)

    main = client.get('/election/proporz-election/connections')
    assert '<h3>Listenverbindungen</h3>' in main

    data = client.get('/election/proporz-election/connections-data').json

    nodes = [node['name'] for node in data['nodes']]
    assert 'FDP' in nodes
    assert 'CVP' in nodes

    links = [
        '{}:{}'.format(link['source'], link['value']) for link in data['links']
    ]
    assert '{}:8'.format(nodes.index('FDP')) in links
    assert '{}:5'.format(nodes.index('CVP')) in links

    chart = client.get('/election/proporz-election/connections-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/connections-data' in chart


def test_view_election_panachage(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/panachage')
    assert '<h3>Panaschierstatistik</h3>' not in main

    assert client.get('/election/majorz-election/panachage-data').json == {}

    chart = client.get('/election/majorz-election/panachage-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/panachage-data' in chart

    upload_proporz_election(client)

    main = client.get('/election/proporz-election/panachage')
    assert '<h3>Panaschierstatistik</h3>' in main

    data = client.get('/election/proporz-election/panachage-data').json

    nodes = [node['name'] for node in data['nodes']]
    assert '-' in nodes
    assert 'FDP' in nodes
    assert 'CVP' in nodes

    links = [link['value'] for link in data['links']]
    assert all((i in links for i in (1, 2, 3, 7)))

    chart = client.get('/election/proporz-election/connections-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/connections-data' in chart


def test_view_election_json(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    data = str(client.get('/election/majorz-election/json').json)
    assert all((expected in data for expected in (
        "Engler", "Stefan", "20", "Schmid", "Martin", "18"
    )))

    data = str(client.get('/election/proporz-election/json').json)
    assert all((expected in data for expected in (
        "Casanova", "Angela", "56", "Caluori", "Corina", "32", "CVP", "FDP"
    )))


def test_view_election_summary(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2014-01-01 12:00"):
        upload_majorz_election(client)
        upload_proporz_election(client)

        assert client.get('/election/majorz-election/summary').json == {
            'date': '2015-01-01',
            'domain': 'federation',
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 1, 'total': 125},
            'title': {'de_CH': 'Majorz Election'},
            'type': 'election',
            'url': 'http://localhost/election/majorz-election',
        }
        assert client.get('/election/proporz-election/summary').json == {
            'date': '2015-01-01',
            'domain': 'federation',
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

    export = client.get('/election/majorz-election/data-xlsx')
    assert export.status == '200 OK'

    export = client.get('/election/proporz-election/data-json')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))

    export = client.get('/election/proporz-election/data-csv')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))

    export = client.get('/election/proporz-election/data-xlsx')
    assert export.status == '200 OK'
