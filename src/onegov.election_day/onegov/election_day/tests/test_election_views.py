from datetime import date
from freezegun import freeze_time
from onegov.election_day.tests import login
from onegov.election_day.tests import upload_majorz_election
from onegov.election_day.tests import upload_proporz_election
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

    export = client.get('/election/proporz-election/data-parties').text
    assert export == (
        'name,votes,mandates\r\nBDP,60387,1\r\nCVP,49117,1\r\nFDP,35134,0\r\n'
    )


def test_view_election_parties_historical(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()
    login(client)

    for id, year, domain, mandates, results in (
        ('e1', 2014, 'federation', 5, 'BDP,2000,5\r\nCVP,1000,0\r\n'),
        ('e2', 2015, 'federation', 5, 'BDP,2001,4\r\nCVP,1001,1\r\n'),
        ('e3', 2016, 'federation', 5, 'BDP,2002,3\r\nCVP,1002,2\r\n'),
        ('e4', 2013, 'federation', 4, 'BDP,2003,2\r\nCVP,1003,2\r\n'),
        ('e5', 2012, 'canton', 5, 'BDP,2004,3\r\nCVP,1004,2\r\n')
    ):
        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = id
        new.form['date'] = date(year, 1, 1)
        new.form['mandates'] = mandates
        new.form['election_type'] = 'proporz'
        new.form['domain'] = domain
        new.form.submit()

        csv = (
            "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
            "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,Listen-Nr,"
            "Partei-ID,Parteibezeichnung,HLV-Nr,ULV-Nr,Anzahl Sitze Liste,"
            "Unveränderte Wahlzettel Liste,Veränderte Wahlzettel Liste,"
            "Kandidatenstimmen unveränderte Wahlzettel,"
            "Zusatzstimmen unveränderte Wahlzettel,"
            "Kandidatenstimmen veränderte Wahlzettel,"
            "Zusatzstimmen veränderte Wahlzettel,Kandidaten-Nr,Gewählt,Name,"
            "Vorname,Stimmen unveränderte Wahlzettel,"
            "Stimmen veränderte Wahlzettel,Stimmen Total aus Wahlzettel,"
            "01 FDP,02 CVP, Anzahl Gemeinden\n"
            "{},3503,56,32,1,0,1,1,19,FDP,1,1,0,0,0,0,0,8,0,101,"
            "nicht gewählt,Casanova,Angela,0,0,0,0,1,1 von 125\n"
            "{},3503,56,32,1,0,1,2,20,CVP,1,2,0,1,0,5,0,0,0,201,"
            "nicht gewählt,Caluori,Corina,1,0,1,2,0,1 von 125\n".format(
                mandates, mandates
            )
        ).encode('utf-8')
        csv_parties = ("Partei,Stimmen,Sitze\n" + results).encode('utf-8')

        mime = 'text/plain'
        upload = client.get('/election/{}/upload'.format(id))
        upload.form['file_format'] = 'sesam'
        upload.form['results'] = Upload('data.csv', csv, mime)
        upload.form['parties'] = Upload('parties.csv', csv_parties, mime)
        upload = upload.form.submit()

        assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
        export = client.get('/election/{}/data-parties'.format(id)).text
        assert results in export

    e1 = client.get('/election/e1/parties-data').json
    e2 = client.get('/election/e2/parties-data').json
    e3 = client.get('/election/e3/parties-data').json
    e4 = client.get('/election/e4/parties-data').json
    e5 = client.get('/election/e5/parties-data').json

    assert e1['groups'] == ['BDP', 'CVP']
    assert e2['groups'] == ['BDP', 'CVP']
    assert e3['groups'] == ['BDP', 'CVP']
    assert e4['groups'] == ['BDP', 'CVP']
    assert e5['groups'] == ['BDP', 'CVP']

    assert e1['labels'] == ['2014']
    assert e2['labels'] == ['2014', '2015']
    assert e3['labels'] == ['2014', '2015', '2016']
    assert e4['labels'] == ['2013']
    assert e5['labels'] == ['2012']


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
    assert 'Blankoliste' in nodes
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
