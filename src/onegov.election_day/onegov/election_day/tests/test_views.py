import onegov.election_day

from datetime import date
from freezegun import freeze_time
from onegov.testing import utils
from webtest import TestApp as Client
from webtest.forms import Upload


COLUMNS = [
    'Bezirk',
    'BFS Nummer',
    'Gemeinde',
    'Ja Stimmen',
    'Nein Stimmen',
    'Stimmberechtigte',
    'Leere Stimmzettel',
    'Ungültige Stimmzettel'
]


def login(client):
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.election_day)


def test_view_login_logout(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/').click('Anmelden')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter1'

    assert "Unbekannter Benutzername oder falsches Passwort" \
        in login.form.submit()
    assert 'Anmelden' in client.get('/')

    login.form['password'] = 'hunter2'
    homepage = login.form.submit().follow()

    assert 'Sie sind angemeldet' in homepage
    assert 'Abmelden' in homepage
    assert 'Anmelden' not in homepage

    assert 'Anmelden' in client.get('/').click('Abmelden').follow()


def test_view_manage(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    assert client.get('/manage', expect_errors=True).status_code == 403

    login(client)

    manage = client.get('/manage')
    assert "Noch keine Wahlen erfasst" in manage
    assert "Noch keine Abstimmungen erfasst" in manage

    new = manage.click('Neue Abstimmung')
    new.form['vote_de'] = 'Vote for a better yesterday'
    new.form['date'] = date(2016, 1, 1)
    new.form['domain'] = 'federation'
    manage = new.form.submit().follow()

    assert "Vote for a better yesterday" in manage
    edit = manage.click('Bearbeiten')
    edit.form['vote_de'] = 'Vote for a better tomorrow'
    manage = edit.form.submit().follow()

    assert "Vote for a better tomorrow" in manage

    delete = manage.click("Löschen")
    assert "Abstimmung löschen" in delete
    assert "Vote for a better tomorrow" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Abstimmungen erfasst" in manage

    new = manage.click('Neue Wahl')
    new.form['election_de'] = 'Elect a new president'
    new.form['date'] = date(2016, 1, 1)
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['mandates'] = 1
    manage = new.form.submit().follow()

    assert "Elect a new president" in manage
    edit = manage.click('Bearbeiten')
    edit.form['election_de'] = 'Elect a new federal councillor'
    manage = edit.form.submit().follow()

    assert "Elect a new federal councillor" in manage

    delete = manage.click("Löschen")
    assert "Wahl löschen" in delete
    assert "Elect a new federal councillor" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Wahlen erfasst" in manage


def test_i18n(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = 'Foo'
    new.form['vote_fr'] = 'Bar'
    new.form['vote_it'] = 'Baz'
    new.form['vote_rm'] = 'Qux'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    homepage = client.get('/')
    assert "Foo" in homepage

    homepage = homepage.click('Français').follow()
    assert "Bar" in homepage

    homepage = homepage.click('Italiano').follow()
    assert "Baz" in homepage

    homepage = homepage.click('Rumantsch').follow()
    assert "Qux" in homepage

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Tick'
    new.form['election_fr'] = 'Trick'
    new.form['election_it'] = 'Track'
    new.form['election_rm'] = 'Quack'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    homepage = client.get('/')
    assert "Quack" in homepage

    homepage = homepage.click('Français').follow()
    assert "Trick" in homepage

    homepage = homepage.click('Italiano').follow()
    assert "Track" in homepage

    homepage = homepage.click('Deutsch').follow()
    assert "Tick" in homepage


def test_pages_cache(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH')

    # make sure codes != 200 are not cached
    anonymous = Client(election_day_app)
    anonymous.get('/vote/0xdeadbeef', status=404)
    anonymous.get('/election/0xdeafbeef', status=404)

    login(client)

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = '0xdeadbeef'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    assert '0xdeadbeef' in anonymous.get('/')
    assert '0xdeadbeef' in anonymous.get('/vote/0xdeadbeef')

    edit = client.get('/vote/0xdeadbeef/edit')
    edit.form['vote_de'] = '0xdeadc0de'
    edit.form.submit()

    assert '0xdeadc0de' in client.get('/')
    assert '0xdeadbeef' in anonymous.get('/')
    assert '0xdeadc0de' in anonymous.get('/', headers=[
        ('Cache-Control', 'no-cache')
    ])

    new = client.get('/manage/new-election')
    new.form['election_de'] = '0xdeafbeef'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert '0xdeafbeef' not in anonymous.get('/')
    assert '0xdeafbeef' in anonymous.get(
        '/', headers=[('Cache-Control', 'no-cache')]
    )


def test_opendata(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()
    assert "Open Data" in client.get('/opendata')


def test_view_latest(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    latest = client.get('/')
    assert "Abstimmung 1. Januar 2013" in latest
    assert "Wahl 1. Januar 2013" in latest


def test_view_latest_json(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    assert client.get('/json').json['results'] == []

    login(client)

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    latest = client.get('/json')
    assert "Abstimmung 1. Januar 2013" in latest
    assert "Wahl 1. Januar 2013" in latest


def test_view_archive(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "archive/2013" in client.get('/')

    archive = client.get('/archive/2013')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-01-01')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-02-02')
    assert "noch keine Wahlen oder Abstimmungen" in archive


def test_view_archive_json(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    archive = client.get('/archive/2013/json')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-01-01/json')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-02-02/json')
    assert archive.json['results'] == []


def test_view_last_modified(election_day_app):
    with freeze_time("2014-01-01 12:00"):
        client = Client(election_day_app)
        client.get('/locale/de_CH').follow()

        login(client)

        new = client.get('/manage/new-vote')
        new.form['vote_de'] = "Vote"
        new.form['date'] = date(2013, 1, 1)
        new.form['domain'] = 'federation'
        new.form.submit()

        new = client.get('/manage/new-election')
        new.form['election_de'] = "Election"
        new.form['date'] = date(2013, 1, 1)
        new.form['mandates'] = 1
        new.form['election_type'] = 'majorz'
        new.form['domain'] = 'federation'
        new.form.submit()

        client = Client(election_day_app)
        client.get('/locale/de_CH').follow()

        for path in (
            '/json',
            '/archive/2013',
            '/election/election',
            '/election/election/json',
            '/election/election/csv',
            '/election/election/xlsx',
            '/vote/vote/',
            '/vote/vote/json',
            '/vote/vote/csv',
            '/vote/vote/xlsx',
        ):
            assert client.get(path).headers.get('Last-Modified') == \
                'Wed, 01 Jan 2014 12:00:00 GMT'


def test_view_election_candidates(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
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

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    candidates = client.get('/election/election/candidates')
    assert all((expected in candidates for expected in (
        "Engler Stefan", "20", "Schmid Martin", "18"
    )))


def test_view_election_lists(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
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

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    lists = client.get('/election/election/lists')
    assert all((expected in lists for expected in ("FDP", "8", "CVP", "5")))


def test_view_election_connections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
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

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    data = client.get('/election/election/connections').json

    nodes = [node['name'] for node in data['nodes']]
    assert 'FDP' in nodes
    assert 'CVP' in nodes

    links = [
        '{}:{}'.format(link['source'], link['value']) for link in data['links']
    ]
    assert '{}:8'.format(nodes.index('FDP')) in links
    assert '{}:5'.format(nodes.index('CVP')) in links


def test_view_election_export(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
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

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    export = client.get('/election/election/json')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))

    export = client.get('/election/election/csv')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))

    export = client.get('/election/election/xlsx')
    assert export.status == '200 OK'
