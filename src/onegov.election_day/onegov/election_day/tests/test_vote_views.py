from freezegun import freeze_time
from onegov.election_day.tests import login, upload_vote
from webtest import TestApp as Client


def test_view_vote(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client)

    response = client.get('/vote/vote')
    assert all((expected in response for expected in (
        "Zug", "Cham", "599", "1711", "80"
    )))


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
