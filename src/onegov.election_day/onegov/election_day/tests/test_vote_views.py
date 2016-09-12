from datetime import date
from freezegun import freeze_time
from webtest import TestApp as Client
from webtest.forms import Upload


def login(client):
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def upload_vote(client):
    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = (
        'Bezirk,ID,Name,Ja Stimmen,Nein Stimmen,'
        'Stimmberechtigte,Leere Stimmzettel,Ungültige Stimmzettel\n'
        ',1711,Zug,3821,7405,16516,80,1\n'
        ',1706,Oberägeri,811,1298,3560,18,\n'
        ',1709,Unterägeri,1096,2083,5245,18,1\n'
        ',1704,Menzingen,599,1171,2917,17,\n'
        ',1701,Baar,3049,5111,13828,54,3\n'
        ',1702,Cham,2190,3347,9687,60,\n'
        ',1703,Hünenberg,1497,2089,5842,15,1\n'
        ',1708,Steinhausen,1211,2350,5989,17,\n'
        ',1707,Risch,1302,1779,6068,17,\n'
        ',1710,Walchwil,651,743,2016,8,\n'
        ',1705,Neuheim,307,522,1289,10,1\n'
    )
    csv = csv.encode('utf-8')

    upload = client.get('/vote/vote/upload')
    upload.form['type'] = 'simple'
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload


def test_view_vote(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client)

    response = client.get('/vote/vote')
    assert all((expected in response for expected in (
        "Zug", "Cham", "599", "1711", "80"
    )))


def test_ballot_map(election_day_app):
    pass
    # todo: map


def test_view_vote_json(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client)

    data = str(client.get('/vote/vote/json').json)
    assert all((expected in data for expected in (
        "Zug", "Cham", "599", "1711", "80"
    )))


def test_view_vote_summary(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2014-01-01 12:00"):
        upload_vote(client)

        assert client.get('/vote/vote/summary').json == {
            'answer': 'rejected',
            'date': '2015-01-01',
            'domain': 'federation',
            'last_modified': '2014-01-01T12:00:00+00:00',
            'nays_percentage': 62.78808066258552,
            'progress': {'counted': 11.0, 'total': 11.0},
            'title': {'de_CH': 'Vote'},
            'type': 'vote',
            'url': 'http://localhost/vote/vote',
            'yeas_percentage': 37.21191933741448,
        }


def test_view_vote_data(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client)

    export = client.get('/vote/vote/data-json')
    assert all((expected in export for expected in ("1711", "Zug", "16516")))

    export = client.get('/vote/vote/data-csv')
    assert all((expected in export for expected in ("1711", "Zug", "16516")))

    export = client.get('/vote/vote/data-xlsx')
    assert export.status == '200 OK'
