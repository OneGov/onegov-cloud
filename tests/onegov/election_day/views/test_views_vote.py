from __future__ import annotations

from freezegun import freeze_time
from onegov.core.utils import module_path
from tests.onegov.election_day.common import import_ech_from_file
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_complex_vote
from tests.onegov.election_day.common import upload_vote
from webtest import TestApp as Client
from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_view_vote_redirect(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
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


def test_view_vote_entities(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
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
        assert data_url in client.get(url).follow()


def test_view_vote_districts(election_day_app_gr: TestApp) -> None:
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
        assert data_url in client.get(url).follow()


def test_view_vote_statistics(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client, canton='gr')
    upload_complex_vote(client, canton='gr')

    for view in (
        'vote/statistics',
        'complex-vote/proposal-statistics',
        'complex-vote/counter-proposal-statistics',
        'complex-vote/tie-breaker-statistics'
    ):
        response = client.get(f'/vote/{view}')
        assert 'Vaz/Obervaz' in response
        assert '13’828' in response


def test_view_vote_json(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client)

    response = client.get('/vote/vote/json')
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    data = response.json
    assert data['ballots'][0]['progress'] == {'counted': 11, 'total': 11}
    assert data['ballots'][0]['type'] == 'proposal'
    assert len(data['ballots'][0]['results']['entities']) == 11
    assert data['ballots'][0]['results']['total']['yeas'] == 16534
    assert data['completed'] == True
    assert data['data'] == {
        'csv': 'http://localhost/vote/vote/data-csv',
        'json': 'http://localhost/vote/vote/data-json'
    }
    assert data['date'] == '2022-01-01'
    assert data['domain'] == 'federation'
    assert data['embed'] == {
        'entities': [
            'http://localhost/vote/vote/proposal-by-entities-map?locale=de_CH',
            'http://localhost/vote/vote/vote-header-widget',
            (
                'http://localhost/vote/vote/proposal-by-entities-table'
                '?locale=de_CH'
            )
        ],
        'statistics': [
            'http://localhost/vote/vote/proposal-statistics-table?locale=de_CH'
        ]
    }
    assert data['media'] == {'maps': {}}
    assert data['progress'] == {'counted': 11, 'total': 11}
    assert data['related_link'] == ''
    assert data['results']['answer'] == 'rejected'
    assert data['title'] == {'de_CH': 'Vote'}
    assert data['type'] == 'vote'
    assert data['url'] == 'http://localhost/vote/vote'


def test_view_vote_summary(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2014-01-01 12:00"):
        upload_vote(client)

        response = client.get('/vote/vote/summary')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'answer': 'rejected',
            'completed': True,
            'date': '2022-01-01',
            'domain': 'federation',
            'last_modified': '2014-01-01T12:00:00+00:00',
            'nays_percentage': 62.78808066258552,
            'progress': {'counted': 11.0, 'total': 11.0},
            'title': {'de_CH': 'Vote'},
            'type': 'vote',
            'url': 'http://localhost/vote/vote',
            'yeas_percentage': 37.21191933741448,
            'turnout': 61.34161218251847
        }


def test_view_vote_data(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client)
    upload_complex_vote(client)

    main = client.get('/vote/vote/data')
    assert '/vote/vote/data-json' in main
    assert '/vote/vote/data-csv' in main

    data = client.get('/vote/vote/data-json')
    assert data.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert data.headers['Content-Disposition'] == 'inline; filename=vote.json'
    assert all((expected in data for expected in ("1711", "Zug", "16516")))

    data = client.get('/vote/vote/data-csv')
    assert data.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert data.headers['Content-Disposition'] == 'inline; filename=vote.csv'
    assert all((expected in data for expected in ("1711", "Zug", "16516")))

    main = client.get('/vote/complex-vote/data')
    assert '/vote/complex-vote/data-json' in main
    assert '/vote/complex-vote/data-csv' in main

    data = client.get('/vote/complex-vote/data-json')
    assert data.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert data.headers['Content-Disposition'] == \
        'inline; filename=complex-vote.json'
    assert all((expected in data for expected in ("1711", "Zug", "16516")))

    data = client.get('/vote/complex-vote/data-csv')
    assert data.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert data.headers['Content-Disposition'] == \
        'inline; filename=complex-vote.csv'
    assert all((expected in data for expected in ("1711", "Zug", "16516")))


def test_views_vote_embedded_widgets(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_complex_vote(client)
    for url in (
        'proposal-by-entities-table',
        'proposal-by-districts-table',
        'proposal-statistics-table',
        'counter-proposal-by-entities-table',
        'counter-proposal-by-districts-table',
        'counter-proposal-statistics-table',
        'tie-breaker-by-entities-table',
        'tie-breaker-by-districts-table',
        'tie-breaker-statistics-table',
        'vote-header-widget',
    ):
        client.get(f'/vote/complex-vote/{url}').maybe_follow()


def test_views_vote_municipal_and_municipality(
    election_day_app_sg: TestApp
) -> None:
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()
    login(client)

    import_ech_from_file(
        client,
        module_path(
            'tests.onegov.election_day',
            'fixtures/multiple/sg/vote-result-delivery_20250518.xml'
        )
    )

    page = client.get('/')

    assert 'Urnengang vom 18. Mai 2025' in page
    assert 'Kantonale Abstimmungen' in page
    assert 'Finanzausgleichsgesetz' in page
    assert 'Kommunale Wahlen und Abstimmungen' in page
    assert 'Zu den kommunalen Wahl- und Abstimmungsergebnissen' in page
    assert '/archive/2025-05-18/municipal' in page

    # verify municipal results
    municipal_page = page.click(
        'Zu den kommunalen Wahl- und Abstimmungsergebnissen')
    assert 'Urnengang vom 18. Mai 2025' in page
    assert 'Kommunale Wahlen und Abstimmungen' in page
    for municipality in (
        'Au', 'Balgach', 'Gaiserwald', 'Gossau', 'Mosnang',
        'Niederhelfenschwil', 'Rheineck', 'St. Gallen',
        'St. Margrethen', 'Wattwil'
    ):
        assert municipality in municipal_page

    # verify municipality detail page
    balgach_page = municipal_page.click('Balgach', index=0)
    assert 'Urnengang vom 18. Mai 2025' in balgach_page
    assert 'Kommunale Wahlen und Abstimmungen' in balgach_page
    assert 'Balgach' in balgach_page
    assert 'Abstimmung' in balgach_page
    t1 = 'betreffend die Hochwasserschutzprojekte «Wolfsbach und'
    assert t1 in balgach_page
    assert 'angenommen' in balgach_page
    assert '74.15' in balgach_page
    t2 = 'Urnenabstimmung betreffend das Hochwasserschutzprojekt «Dorfbach»'
    assert t2 in balgach_page
    assert '75.15' in balgach_page
    # municipality name must be capitalized in the vote header
    vote_page = balgach_page.click('Dorfbach').maybe_follow()
    assert vote_page.status_code == 200
    assert 'Balgach' in vote_page


def test_view_vote_shows_long_title(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['title_de'] = 'The Long Title of the Vote'
    new.form['short_title_de'] = 'Short Title'
    new.form['date'] = '2022-01-01'
    new.form['domain'] = 'federation'
    new.form['type'] = 'simple'
    new.form.submit().follow()

    csv = (
        'entity_id,yeas,nays,eligible_voters,empty,invalid,status,type,counted\n'
        '1701,3049,5111,13828,54,3,final,proposal,true\n'
    )
    upload = client.get('/vote/short-title/upload')
    upload.form['proposal'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain')
    upload.form.submit()

    archive = client.get('/archive/2022-01-01')
    assert 'The Long Title of the Vote' in archive
    assert 'Short Title' not in archive
