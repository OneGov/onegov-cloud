from datetime import date
from freezegun import freeze_time
from webtest import TestApp as Client
from webtest.forms import Upload


def login(client):
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def upload_majorz_election(client):
    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Majorz Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = (
        "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
        "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,"
        "Ungueltige Stimmen,Kandidaten-Nr,Gewaehlt,Name,Vorname,Stimmen,"
        "Anzahl Gemeinden\n"
    )
    csv += "2,3503,56,25,0,4,1,0,1,Gewaehlt,Engler,Stefan,20,1 von 1\n"
    csv += "2,3503,56,25,0,4,1,0,2,Gewaehlt,Schmid,Martin,18,1 von 1\n"
    csv = csv.encode('utf-8')

    upload = client.get('/election/majorz-election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload


def upload_proporz_election(client):
    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Proporz Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
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
    )
    csv += (
        "5,3503,56,32,1,0,1,1,19,FDP,1,1,0,0,0,0,0,8,0,101,"
        "nicht gewählt,Casanova,Angela,0,0,0,0,0,1 von 1\n"
    )
    csv += (
        "5,3503,56,32,1,0,1,2,20,CVP,1,2,0,1,0,5,0,0,0,201,"
        "nicht gewählt,Caluori,Corina,1,0,1,0,0,1 von 1\n"
    )
    csv = csv.encode('utf-8')

    upload = client.get('/election/proporz-election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload


def test_view_election(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    response = client.get('/election/majorz-election')
    assert all((expected in response for expected in (
        "Engler", "Stefan", "20", "Schmid", "Martin", "18", "Mutten",
        "Brusio", "Noch nicht ausgezählt"
    )))

    response = client.get('/election/proporz-election')
    assert all((expected in response for expected in (
        "Casanova", "Angela", "56", "Caluori", "Corina", "32", "CVP", "FDP",
        "Mutten", "Brusio", "Noch nicht ausgezählt"
    )))


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


def test_view_election_lists(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    lists = client.get('/election/majorz-election/lists')
    assert lists.json['results'] == []

    chart = client.get('/election/majorz-election/lists-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/lists' in chart

    lists = client.get('/election/proporz-election/lists')
    assert all((expected in lists for expected in ("FDP", "8", "CVP", "5")))

    chart = client.get('/election/proporz-election/lists-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/lists' in chart


def test_view_election_connections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    assert client.get('/election/majorz-election/connections').json == {}

    chart = client.get('/election/majorz-election/connections-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/connections' in chart

    data = client.get('/election/proporz-election/connections').json

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
    assert '/election/proporz-election/connections' in chart


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
            'progress': {'counted': 1, 'total': 1},
            'title': {'de_CH': 'Majorz Election'},
            'type': 'election',
            'url': 'http://localhost/election/majorz-election',
        }
        assert client.get('/election/proporz-election/summary').json == {
            'date': '2015-01-01',
            'domain': 'federation',
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 1, 'total': 1},
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
