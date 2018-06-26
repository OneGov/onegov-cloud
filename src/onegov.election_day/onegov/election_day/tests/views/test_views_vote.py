from freezegun import freeze_time
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import upload_complex_vote
from onegov.election_day.tests.common import upload_vote
from webtest import TestApp as Client


def test_view_vote_redirect(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_complex_vote(client)

    response = client.get('/vote/vote')
    assert response.status == '302 Found'
    assert 'vote/vote/entities' in response.headers['Location']

    response = client.get('/vote/complex-vote')
    assert response.status == '302 Found'
    assert 'complex-vote/proposal-entities' in response.headers['Location']


def test_view_vote_entities(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_complex_vote(client)

    for view in (
        'vote/entities',
        'complex-vote/proposal-entities',
        'complex-vote/counter-proposal-entities',
        'complex-vote/tie-breaker-entities'
    ):
        response = client.get(f'/vote/{view}')
        assert 'Walchwil' in response
        assert '46.70' in response
        assert '37.21' in response

        data_url = response.pyquery('.entities-map')[0].attrib['data-dataurl']
        assert data_url.endswith('/by-entity')
        assert client.get(data_url).json['1701']['counted'] is True

        url = response.pyquery('.entities-map')[0].attrib['data-embed-source']
        assert data_url in client.get(url)


def test_view_vote_districts(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client, canton='gr')
    upload_complex_vote(client, canton='gr')

    for view in (
        'vote/districts',
        'complex-vote/proposal-districts',
        'complex-vote/counter-proposal-districts',
        'complex-vote/tie-breaker-districts'
    ):
        response = client.get(f'/vote/{view}')
        assert 'Landquart' in response
        assert '37.37' in response

        data_url = response.pyquery('.districts-map')[0].attrib['data-dataurl']
        assert data_url.endswith('/by-district')
        assert client.get(data_url).json['Landquart']['counted'] is False

        url = response.pyquery('.districts-map')[0].attrib['data-embed-source']
        assert data_url in client.get(url)


def test_view_vote_json(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client)

    response = client.get('/vote/vote/json')
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    assert all((expected in str(response.json) for expected in (
        "Zug", "Cham", "599", "1711", "80"
    )))


def test_view_vote_summary(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2014-01-01 12:00"):
        upload_vote(client)

        response = client.get('/vote/vote/summary')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'answer': 'rejected',
            'completed': True,
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
