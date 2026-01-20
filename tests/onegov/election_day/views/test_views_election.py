from __future__ import annotations

from freezegun import freeze_time
from onegov.election_day.layouts import ElectionLayout
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import MAJORZ_HEADER
from tests.onegov.election_day.common import upload_majorz_election
from tests.onegov.election_day.common import upload_party_results
from tests.onegov.election_day.common import upload_proporz_election
from webtest import TestApp as Client
from webtest.forms import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def round_(n: int, z: int) -> float:
    return round(100 * n / z, 2)


def test_view_election_redirect(election_day_app_gr: TestApp) -> None:
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


def test_view_election_candidates(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    # Majorz election intermediate results
    upload_majorz_election(client, status='interim')

    # ... main
    candidates = client.get('/election/majorz-election/candidates')
    assert all((expected in candidates for expected in (
        "Engler Stefan", "20", "Pendent", "Schmid Martin", "18", "Pendent"
    )))

    # Majorz election final results
    upload_majorz_election(client, status='final')

    # ... main
    candidates = client.get('/election/majorz-election/candidates')
    assert all((expected in candidates for expected in (
        "Engler Stefan", "20", "Ja", "Schmid Martin", "18", "Ja"
    )))

    # ... bar chart data (with filters)
    for suffix in ('', '?limit=', '?limit=a', '?limit=0'):
        candidates = client.get(
            f'/election/majorz-election/candidates-data{suffix}'
        )
        assert {r['text']: r['value'] for r in candidates.json['results']} == {
            'Engler Stefan': 20, 'Schmid Martin': 18
        }

    candidates = client.get(
        '/election/majorz-election/candidates-data?limit=1'
    )
    assert {r['text']: r['value'] for r in candidates.json['results']} == {
        'Engler Stefan': 20
    }

    candidates = client.get(
        '/election/majorz-election/candidates-data?entity=Vaz/Obervaz'
    )
    assert {r['text']: r['value'] for r in candidates.json['results']} == {
        'Engler Stefan': 20, 'Schmid Martin': 18
    }

    # ... embedded chart (with filters)
    chart = client.get('/election/majorz-election/candidates-chart')
    assert '/election/majorz-election/candidates' in chart

    chart = client.get(
        '/election/majorz-election/candidates-chart?entity=Filisur'
    )
    assert 'entity=Filisur' in chart

    # ... embedded table (with filters)
    table = client.get('/election/majorz-election/candidates-table')
    assert 'data-text="20"' in table

    table = client.get(
        '/election/majorz-election/candidates-table?entity=Vaz/Obervaz'
    )
    assert 'data-text="20"' in table

    table = client.get(
        '/election/majorz-election/candidates-table?entity=Filisur'
    )
    assert 'data-text=' not in table

    # Proporz election intermediate results
    upload_proporz_election(client, status='interim')

    # ....main
    candidates = client.get('/election/proporz-election/candidates')
    assert all((expected in candidates for expected in (
        "Caluori Corina", "1", "Pendent", "Casanova Angela", "0", "Pendent"
    )))

    # Proporz election final results
    upload_proporz_election(client, status='final')

    # ....main
    candidates = client.get('/election/proporz-election/candidates')
    assert all((expected in candidates for expected in (
        "Caluori Corina", "1", "Nein", "Casanova Angela", "0", "Nein"
    )))

    # ... bar chart data (with filters)
    for suffix in ('', '?limit=', '?limit=a', '?limit=0'):
        candidates = client.get(
            f'/election/proporz-election/candidates-data{suffix}'
        )
        assert candidates.json['results'] == []

    candidates = client.get(
        '/election/proporz-election/candidates-data?elected=False&limit=1'
    )
    assert {r['text']: r['value'] for r in candidates.json['results']} == {
        'Caluori Corina': 2
    }

    candidates = client.get(
        '/election/majorz-election/candidates-data?elected=False&'
        'entity=Vaz/Obervaz'
    )
    assert {r['text']: r['value'] for r in candidates.json['results']} == {
        'Engler Stefan': 20, 'Schmid Martin': 18
    }

    # ... embedded chart (with filters)
    chart = client.get('/election/proporz-election/candidates-chart')
    assert '/election/proporz-election/candidates' in chart

    chart = client.get(
        '/election/proporz-election/candidates-chart?entity=Filisur'
    )
    assert 'entity=Filisur' in chart

    # ... ebmedded table (with filters)
    table = client.get('/election/proporz-election/candidates-table')
    assert 'data-text="2"' in table

    table = client.get(
        '/election/proporz-election/candidates-table?entity=Vaz/Obervaz'
    )
    assert 'data-text="2"' in table

    table = client.get(
        '/election/proporz-election/candidates-table?entity=Filisur'
    )
    assert 'data-text=' not in table


def test_view_election_candidate_by_entity(
    election_day_app_gr: TestApp
) -> None:

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client, status='final')
    upload_proporz_election(client, status='final')

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
        assert data['Engler']['3506']['counted'] is True
        assert data['Engler']['3506']['percentage'] == round_(20, 21)
        assert data['Schmid']['3506']['counted'] is True
        assert data['Schmid']['3506']['percentage'] == round_(18, 21)

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
        assert data['Caluori']['3506']['counted'] is True
        assert data['Caluori']['3506']['percentage'] == round_(2, 14)
        assert data['Casanova']['3506']['counted'] is True
        assert data['Casanova']['3506']['percentage'] == 0.0

    # test for incomplete majorz
    upload_majorz_election(client, status='unknown')
    upload_proporz_election(client, status='final')
    for url in (
        '/election/majorz-election/candidate-by-entity',
        '/election/majorz-election/candidate-by-entity-chart'
    ):
        view = client.get(url)
        assert '/by-entity">Engler Stefan</option>' in view
        assert '/by-entity">Schmid Martin</option>' in view

    # test for incomplete proporz


def test_view_election_candidate_by_district(
    election_day_app_gr: TestApp
) -> None:

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client, status='final')
    upload_proporz_election(client, status='final')

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
        assert set(data['Engler']['Bernina']['entities']) == {3561, 3551}
        assert data['Engler']['Bernina']['counted'] is False
        assert data['Engler']['Bernina']['percentage'] == 0.0
        assert set(data['Schmid']['Bernina']['entities']) == {3561, 3551}
        assert data['Schmid']['Bernina']['counted'] is False
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
        assert set(data['Caluori']['Bernina']['entities']) == {3561, 3551}
        assert data['Caluori']['Bernina']['counted'] is False
        assert data['Caluori']['Bernina']['percentage'] == 0.0
        assert set(data['Casanova']['Bernina']['entities']) == {3561, 3551}
        assert data['Casanova']['Bernina']['counted'] is False
        assert data['Casanova']['Bernina']['percentage'] == 0.0


def test_view_election_statistics(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    statistics = client.get('/election/majorz-election/statistics')
    assert all(expected in statistics for expected in (
        "1 von 101", "Grüsch", "56", "25", "21", "41", "Noch nicht ausgezählt"
    ))

    statistics = client.get('/election/proporz-election/statistics')
    assert all(expected in statistics for expected in (
        "1 von 101", "Grüsch", "56", "32", "31", "153", "Noch nicht ausgezählt"
    ))


def test_view_election_lists(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    # Majorz election
    upload_majorz_election(client)

    # ... main
    main = client.get('/election/majorz-election/lists')
    assert '<h3>Listen</h3>' not in main

    # ... bar chart data
    data = client.get('/election/majorz-election/lists-data')
    assert data.json['results'] == []

    # ... embedded chart
    chart = client.get('/election/majorz-election/lists-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/lists' in chart

    # .... embedded table
    table = client.get('/election/majorz-election/lists-table')
    assert 'data-text=' not in table

    # Proporz election
    upload_proporz_election(client)

    # ... main
    main = client.get('/election/proporz-election/lists')
    assert '<h3>Listen</h3>' in main

    # ... bar chart data (with filters)
    for suffix in ('', '?limit=', '?limit=a', '?limit=0'):
        data = client.get(f'/election/proporz-election/lists-data{suffix}')
        assert {r['text']: r['value'] for r in data.json['results']} == {
            'FDP': 8,
            'CVP': 6
        }

    data = client.get('/election/proporz-election/lists-data?limit=1')
    assert {r['text']: r['value'] for r in data.json['results']} == {
        'FDP': 8,
    }

    data = client.get(
        '/election/proporz-election/lists-data?entity=Vaz/Obervaz'
    )
    assert data.json['results']

    data = client.get('/election/proporz-election/lists-data?entity=Filisur')
    assert not data.json['results']

    # ... embedded chart (with filters)
    chart = client.get('/election/proporz-election/lists-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/lists-data' in chart

    chart = client.get('/election/proporz-election/lists-chart?entity=Filisur')
    assert 'entity=Filisur' in chart

    # ... embedded table (with filters)
    table = client.get('/election/proporz-election/lists-table')
    assert 'data-text="8"' in table

    table = client.get(
        '/election/proporz-election/lists-table?entity=Vaz/Obervaz'
    )
    assert 'data-text="8"' in table

    table = client.get('/election/proporz-election/lists-table?entity=Filisur')
    assert 'data-text=' not in table


def test_view_election_list_by_entity(election_day_app_gr: TestApp) -> None:
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
        assert data['CVP']['3506']['counted'] is True
        assert data['CVP']['3506']['percentage'] == round_(6, 14)
        assert data['FDP']['3506']['counted'] is True
        assert data['FDP']['3506']['percentage'] == round_(8, 14)


def test_view_election_list_by_district(election_day_app_gr: TestApp) -> None:
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
        assert set(data['CVP']['Bernina']['entities']) == {3561, 3551}
        assert data['CVP']['Bernina']['counted'] is False
        assert data['CVP']['Bernina']['percentage'] == 0.0
        assert set(data['FDP']['Bernina']['entities']) == {3561, 3551}
        assert data['FDP']['Bernina']['counted'] is False
        assert data['FDP']['Bernina']['percentage'] == 0.0


def test_view_election_party_strengths(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()
    login(client)

    # Majorz election
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/party-strengths')
    assert '<h4>Parteistärken</h4>' not in main

    parties = client.get('/election/majorz-election/party-strengths-data').json
    assert parties['results'] == []

    chart = client.get('/election/majorz-election/party-strengths-chart')
    assert chart.status_code == 200
    assert '/election/majorz-election/party-strengths' in chart

    # Proporz election
    upload_proporz_election(client)
    upload_party_results(client)

    main = client.get('/election/proporz-election/party-strengths')
    assert '<h4>Parteistärken</h4>' in main

    parties = client.get(
        '/election/proporz-election/party-strengths-data').json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2022']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 5
    assert parties['results']

    chart = client.get('/election/proporz-election/party-strengths-chart')
    assert chart.status_code == 200
    assert '/election/proporz-election/party-strengths-data' in chart

    assert 'panel_2022' in client.get(
        '/election/proporz-election/party-strengths-table'
    )
    assert 'panel_2022' in client.get(
        '/election/proporz-election/party-strengths-table?year=2022'
    )
    assert 'panel_2022' not in client.get(
        '/election/proporz-election/party-strengths-table?year=2018'
    )

    export = client.get('/election/proporz-election/data-parties-csv').text
    lines = [l for l in export.split('\r\n') if l]
    assert lines == [
        'domain,domain_segment,year,id,'
        'name,name_de_CH,name_fr_CH,name_it_CH,name_rm_CH,'
        'total_votes,color,mandates,votes,'
        'voters_count,voters_count_percentage,panachage_votes_from_1,'
        'panachage_votes_from_2,panachage_votes_from_3,'
        'panachage_votes_from_999',
        'federation,,2022,1,BDP,BDP,,,,11270,#efb52c,'
        '1,60387,603.01,41.73,,11,12,100',
        'federation,,2022,2,CVP,CVP,,,,11270,#ff6300,'
        '1,49117,491.02,33.98,21,,22,200',
        'federation,,2022,3,FDP,FDP,,,,11270,,'
        '0,35134,351.04,24.29,31,32,,300',
    ]

    export = client.get('/election/proporz-election/data-parties-json').json
    assert export == [
        {
            'color': '#efb52c',
            'domain': 'federation',
            'domain_segment': None,
            'id': '1',
            'mandates': 1,
            'name': 'BDP',
            'name_de_CH': 'BDP',
            'name_fr_CH': None,
            'name_it_CH': None,
            'name_rm_CH': None,
            'panachage_votes_from_1': None,
            'panachage_votes_from_2': 11,
            'panachage_votes_from_3': 12,
            'panachage_votes_from_999': 100,
            'total_votes': 11270,
            'voters_count': 603.01,
            'voters_count_percentage': 41.73,
            'votes': 60387,
            'year': 2022
        },
        {
            'color': '#ff6300',
            'domain': 'federation',
            'domain_segment': None,
            'id': '2',
            'mandates': 1,
            'name': 'CVP',
            'name_de_CH': 'CVP',
            'name_fr_CH': None,
            'name_it_CH': None,
            'name_rm_CH': None,
            'panachage_votes_from_1': 21,
            'panachage_votes_from_2': None,
            'panachage_votes_from_3': 22,
            'panachage_votes_from_999': 200,
            'total_votes': 11270,
            'voters_count': 491.02,
            'voters_count_percentage': 33.98,
            'votes': 49117,
            'year': 2022
        },
        {
            'color': None,
            'domain': 'federation',
            'domain_segment': None,
            'id': '3',
            'mandates': 0,
            'name': 'FDP',
            'name_de_CH': 'FDP',
            'name_fr_CH': None,
            'name_it_CH': None,
            'name_rm_CH': None,
            'panachage_votes_from_1': 31,
            'panachage_votes_from_2': 32,
            'panachage_votes_from_3': None,
            'panachage_votes_from_999': 300,
            'total_votes': 11270,
            'voters_count': 351.04,
            'voters_count_percentage': 24.29,
            'votes': 35134,
            'year': 2022
        }
    ]

    # Historical data with translations
    csv_parties = (
        'year,name,name_fr_ch,id,total_votes,color,mandates,'
        'votes,voters_count,voters_count_percentage\r\n'
        '2022,BDP,,1,60000,#efb52c,1,10000,100,16.67\r\n'
        '2022,Die Mitte,Le Centre,2,60000,#ff6300,1,30000,300,50\r\n'
        '2022,FDP,,3,60000,#4068c8,0,20000,200,33.33\r\n'
        '2018,BDP,,1,40000,#efb52c,1,1000,10,2.5\r\n'
        '2018,CVP,PDC,2,40000,#ff6300,1,15000,150.7,37.67\r\n'
        '2018,FDP,,3,40000,#4068c8,1,10000,100,25.0\r\n'
    ).encode('utf-8')

    upload = client.get('/election/proporz-election/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    parties = client.get(
        '/election/proporz-election/party-strengths-data'
    ).json
    assert parties['groups'] == ['BDP', 'Die Mitte', 'FDP']
    assert parties['labels'] == ['2018', '2022']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 5
    assert parties['results']

    parties = {
        '{}-{}'.format(party['item'], party['group']): party
        for party in parties['results']
    }
    assert parties['2018-BDP']['color'] == '#efb52c'
    assert parties['2022-BDP']['color'] == '#efb52c'
    assert parties['2018-Die Mitte']['color'] == '#ff6300'
    assert parties['2022-Die Mitte']['color'] == '#ff6300'
    assert parties['2018-FDP']['color'] == '#4068c8'
    assert parties['2022-FDP']['color'] == '#4068c8'

    assert parties['2018-BDP']['active'] is False
    assert parties['2018-Die Mitte']['active'] is False
    assert parties['2018-FDP']['active'] is False
    assert parties['2022-BDP']['active'] is True
    assert parties['2022-Die Mitte']['active'] is True
    assert parties['2022-FDP']['active'] is True

    assert parties['2018-BDP']['value']['front'] == 1
    assert parties['2018-Die Mitte']['value']['front'] == 1
    assert parties['2018-FDP']['value']['front'] == 1
    assert parties['2022-BDP']['value']['front'] == 1
    assert parties['2022-Die Mitte']['value']['front'] == 1
    assert parties['2022-FDP']['value']['front'] == 0

    assert parties['2018-BDP']['value']['back'] == 2.5
    assert parties['2018-Die Mitte']['value']['back'] == 37.5
    assert parties['2018-FDP']['value']['back'] == 25
    assert parties['2022-BDP']['value']['back'] == 16.7
    assert parties['2022-Die Mitte']['value']['back'] == 50
    assert parties['2022-FDP']['value']['back'] == 33.3

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

    # with exact voters counts
    edit = client.get('/election/proporz-election/edit')
    edit.form['voters_counts'] = True
    edit.form['exact_voters_counts'] = True
    edit.form.submit()

    assert '>10.00<' in client.get(
        '/election/proporz-election/party-strengths'
    )
    data = client.get('/election/proporz-election/party-strengths-data').json
    assert data['results'][0]['value']['back'] == 16.67
    data = client.get('/election/proporz-election/json').json
    assert data['parties']['2']['2018']['voters_count']['total'] == 150.7

    # with rounded voters counts
    edit = client.get('/election/proporz-election/edit')
    edit.form['exact_voters_counts'] = False
    edit.form.submit()

    assert '>10<' in client.get('/election/proporz-election/party-strengths')
    data = client.get('/election/proporz-election/party-strengths-data').json
    assert data['results'][0]['value']['back'] == 16.67
    data = client.get('/election/proporz-election/json').json
    assert data['parties']['2']['2018']['voters_count']['total'] == 151

    # translations
    client.get('/locale/fr_CH')
    parties = client.get(
        '/election/proporz-election/party-strengths-data').json
    assert parties['groups'] == ['BDP', 'Le Centre', 'FDP']
    results = client.get('/election/proporz-election/party-strengths').text
    assert 'Le Centre' in results
    assert 'PDC' in results
    assert 'BDP' in results


def test_view_election_connections(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)

    main = client.get('/election/majorz-election/connections')
    assert '<h4>Listenverbindungen</h4>' not in main

    assert client.get('/election/majorz-election/connections-data').json == {}

    chart = client.get('/election/majorz-election/connections-chart')
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
    assert '/election/proporz-election/connections-data' in chart

    data = client.get('/election/proporz-election/data-list-connections').json
    assert data == {
        '1': {
            'subconns': {
                '1': {'lists': {'FDP': 8}, 'total_votes': 8},
                '2': {'lists': {'CVP': 6}, 'total_votes': 6}
            },
            'total_votes': 14
        }
    }


def test_view_election_lists_panachage_majorz(
    election_day_app_gr: TestApp
) -> None:

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


def test_view_election_lists_panachage_proporz(
    election_day_app_gr: TestApp
) -> None:

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_proporz_election(client)

    main = client.get('/election/proporz-election/lists-panachage')
    assert '<h4>Panaschierstatistik</h4>' in main

    data = client.get('/election/proporz-election/lists-panachage-data').json

    nodes = [node['name'] for node in data['nodes']]
    assert 'Blankoliste' in nodes
    assert 'FDP' in nodes
    assert 'CVP' in nodes

    # value is the thickness of the line
    links = sorted([(r['target'], r['value']) for r in data['links']])
    # List 1 gets 1 vote from list 2
    # List 2 gets 2 votes from list 1
    # 4 represents target index of list 2 in nodes on the right side
    # 3 represents target index of list 1 in nodes on the right side
    assert links == [(3, 1), (4, 2)]


def test_view_election_parties_panachage(election_day_app_gr: TestApp) -> None:
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
        11, 12, 100,
        21, 22, 200,
        31, 32, 300,
    )))


def test_view_election_json(election_day_app_gr: TestApp) -> None:
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


def test_view_election_summary(election_day_app_gr: TestApp) -> None:
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
            'date': '2022-01-01',
            'domain': 'federation',
            'elected': [['Stefan', 'Engler'], ['Martin', 'Schmid']],
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 1, 'total': 101},
            'title': {'de_CH': 'Majorz Election'},
            'type': 'election',
            'url': 'http://localhost/election/majorz-election',
            'turnout': 44.642857142857146
        }

        response = client.get('/election/proporz-election/summary')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'completed': False,
            'date': '2022-01-01',
            'domain': 'federation',
            'elected': [],
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 1, 'total': 101},
            'title': {'de_CH': 'Proporz Election'},
            'type': 'election',
            'url': 'http://localhost/election/proporz-election',
            'turnout': 57.14285714285714
        }


def test_view_election_data(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    upload_proporz_election(client)

    main = client.get('/election/majorz-election/data')
    assert '/election/majorz-election/data-json' in main
    assert '/election/majorz-election/data-csv' in main

    data = client.get('/election/majorz-election/data-json')
    assert data.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert data.headers['Content-Disposition'] == (
        'inline; filename=majorz-election.json')
    assert all((expected in data for expected in ("3506", "Engler", "20")))

    data = client.get('/election/majorz-election/data-csv')
    assert data.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert data.headers['Content-Disposition'] == (
        'inline; filename=majorz-election.csv')
    assert all((expected in data for expected in ("3506", "Engler", "20")))

    main = client.get('/election/proporz-election/data')
    assert '/election/proporz-election/data-json' in main
    assert '/election/proporz-election/data-csv' in main

    data = client.get('/election/proporz-election/data-json')
    assert data.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert data.headers['Content-Disposition'] == (
        'inline; filename=proporz-election.json')
    assert all((expected in data for expected in ("FDP", "Caluori", "56")))

    data = client.get('/election/proporz-election/data-csv')
    assert data.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert data.headers['Content-Disposition'] == (
        'inline; filename=proporz-election.csv')
    assert all((expected in data for expected in ("FDP", "Caluori", "56")))


def test_view_election_tacit(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'Tacit Election'
    new.form['date'] = '2022-01-01'
    new.form['mandates'] = 2
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['tacit'] = True
    new.form.submit()

    csv = MAJORZ_HEADER
    csv += (
        "final,,3506,True,56,0,0,0,0,0,1,True,Engler,Stefan,0,\n"
        "final,,3506,True,56,0,0,0,0,0,2,True,Schmid,Martin,0,\n"
    )

    upload = client.get('/election/tacit-election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()
    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    candidates = client.get('/election/tacit-election/candidates')
    assert "Engler Stefan" in candidates
    assert "Schmid Martin" in candidates
    assert "Wahlbeteiligung" not in candidates


def test_view_election_relations(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'First Election'
    new.form['date'] = '2022-01-01'
    new.form['mandates'] = 2
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'Second Election'
    new.form['date'] = '2022-01-02'
    new.form['mandates'] = 2
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['related_elections_historical'] = ['first-election']
    new.form['related_elections_other'] = ['first-election']
    new.form.submit()

    csv = MAJORZ_HEADER
    csv += (
        "final,,3506,True,56,0,0,0,0,0,1,True,Engler,Stefan,0,\n"
        "final,,3506,True,56,0,0,0,0,0,2,True,Schmid,Martin,0,\n"
    )

    for count in ('first', 'second'):
        upload = client.get(f'/election/{count}-election/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload(
            'data.csv', csv.encode('utf-8'), 'text/plain')
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


def test_views_election_embedded_widgets(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_majorz_election(client)
    for tab_name in ElectionLayout.tabs_with_embedded_tables:
        client.get(f'/election/majorz-election/{tab_name}-table')
