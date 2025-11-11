from __future__ import annotations

from freezegun import freeze_time
from onegov.election_day.layouts import ElectionCompoundPartLayout
from tests.onegov.election_day.common import create_election_compound
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_election_compound
from tests.onegov.election_day.common import upload_party_results
from webtest import TestApp as Client
from webtest.forms import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_view_election_compound_part_redirect(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client, canton='bl')

    response = client.get('/elections-part/elections/superregion/region-1')
    assert response.status == '302 Found'
    assert '/elections-part/elections/superregion/region-1/districts' in (
        response.headers['Location'])


def test_view_election_compound_part_districts(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, canton='bl')

    districts = client.get(
        '/elections-part/elections/superregion/region-1/districts'
    )
    assert "Allschwil" in districts
    assert '0 von 5' in districts
    assert "1 von 2" in districts

    map = client.get(
        '/elections-part/elections/superregion/region-1/districts-map'
    )
    assert (
        '/elections-part/elections/superregion/region-1/by-district'
    ) in map

    data = client.get(
        '/elections-part/elections/superregion/region-1/by-district'
    ).json
    assert data == {
        'Allschwil': {
            'counted': False,
            'entities': [2762, 2774],
            'link': 'http://localhost/election/regional-election-b',
            'mandates': '0 / 5',
            'percentage': 100.0,
            'progress': '1 / 2',
            'votes': 0
        }
    }


def test_view_election_compound_part_elected_candidates(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, canton='bl')

    candidates = client.get(
        '/elections-part/elections/superregion/region-1/candidates'
    )
    assert "Sieger Hans" in candidates
    assert "regional-election-b" in candidates
    assert "Allschwil" in candidates


def test_view_election_compound_part_party_strengths(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    create_election_compound(client, canton='bl', voters_counts=False)
    upload_party_results(
        client,
        slug='elections/elections',
        domain='superregion',
        domain_segment='Region 1'
    )

    # main view
    main = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths'
    )
    assert '<h3>Parteistärken</h3>' in main

    # chart data
    parties = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-data'
    ).json
    assert parties['groups'] == ['BDP', 'CVP', 'FDP']
    assert parties['labels'] == ['2022']
    assert parties['maximum']['back'] == 100
    assert parties['maximum']['front'] == 5
    assert parties['results']

    # embedded chart
    chart = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-chart'
    )
    assert chart.status_code == 200
    assert (
        '/elections-part/elections/superregion/region-1/party-strengths-data'
    ) in chart

    # embedded tables
    assert 'panel_2022' in client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-table'
    )
    assert 'panel_2022' in client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-table'
        '?year=2022'
    )
    assert 'panel_2022' not in client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-table'
        '?year=2018'
    )

    # json
    assert client.get(
        '/elections-part/elections/superregion/region-1/json'
    ).json['parties'] == {
        '1': {
            '2022': {
                'name': 'BDP',
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 417.3, 'total': 603.01},
                'votes': {'permille': 5358, 'total': 60387}
            }
        },
        '2': {
            '2022': {
                'name': 'CVP',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 339.8, 'total': 491.02},
                'votes': {'permille': 4358, 'total': 49117}
            }
        },
        '3': {
            '2022': {
                'name': 'FDP',
                'color': None,
                'mandates': 0,
                'voters_count': {'permille': 242.9, 'total': 351.04},
                'votes': {'permille': 3117, 'total': 35134}
            }
        }
    }

    # Historical data with translations
    csv_parties = (
        'domain,domain_segment,year,name,name_fr_ch,id,total_votes,color,'
        'mandates,votes,voters_count,voters_count_percentage\r\n'
        'superregion,Region 1,2022,'
        'BDP,,1,60000,#efb52c,1,10000,100,16.67\r\n'
        'superregion,Region 1,2022,'
        'Die Mitte,Le Centre,2,60000,#ff6300,1,30000,300,50\r\n'
        'superregion,Region 1,2022,'
        'FDP,,3,60000,#4068c8,0,20000,200,33.33\r\n'
        'superregion,Region 1,2018,'
        'BDP,,1,40000,#efb52c,1,1000,10,2.5\r\n'
        'superregion,Region 1,2018,'
        'CVP,PDC,2,40000,#ff6300,1,15000,150.7,37.67\r\n'
        'superregion,Region 1,2018,'
        'FDP,,3,40000,#4068c8,1,10000,100,25.0\r\n'
    ).encode('utf-8')

    upload = client.get('/elections/elections/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
    assert "erfolgreich hochgeladen" in upload

    parties = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-data'
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

    results = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths'
    ).text
    assert '2.5%' in results
    assert '16.7%' in results
    assert '14.2%' in results

    assert '37.5%' in results
    assert '50.0%' in results
    assert '12.5%' in results

    assert '25.0%' in results
    assert '33.3%' in results
    assert '8.3%' in results

    assert client.get(
        '/elections-part/elections/superregion/region-1/json'
    ).json['parties'] == {
        '1': {
            '2018': {
                'name': 'BDP',
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 25.0, 'total': 10.0},
                'votes': {'permille': 25, 'total': 1000}
            },
            '2022': {
                'name': 'BDP',
                'color': '#efb52c',
                'mandates': 1,
                'voters_count': {'permille': 166.7, 'total': 100.0},
                'votes': {'permille': 167, 'total': 10000}
            }
        },
        '2': {
            '2018': {
                'name': 'CVP',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 376.7, 'total': 150.7},
                'votes': {'permille': 375, 'total': 15000}
            },
            '2022': {
                'name': 'Die Mitte',
                'color': '#ff6300',
                'mandates': 1,
                'voters_count': {'permille': 500.0, 'total': 300.0},
                'votes': {'permille': 500, 'total': 30000}
            }
        },
        '3': {
            '2018': {
                'name': 'FDP',
                'color': '#4068c8',
                'mandates': 1,
                'voters_count': {'permille': 250.0, 'total': 100.0},
                'votes': {'permille': 250, 'total': 10000}
            },
            '2022': {
                'name': 'FDP',
                'color': '#4068c8',
                'mandates': 0,
                'voters_count': {'permille': 333.3, 'total': 200.0},
                'votes': {'permille': 333, 'total': 20000}
            }
        }
    }

    # with exact voters counts
    edit = client.get('/elections/elections/edit')
    edit.form['voters_counts'] = True
    edit.form.submit()

    assert '>10.00<' in client.get(
        '/elections-part/elections/superregion/region-1/party-strengths'
    )
    data = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-data'
    ).json
    assert data['results'][0]['value']['back'] == 16.67
    data = client.get(
        '/elections-part/elections/superregion/region-1/json'
    ).json
    assert data['parties']['2']['2018']['voters_count']['total'] == 150.7

    # with rounded voters counts
    edit = client.get('/elections/elections/edit')
    edit.form['exact_voters_counts'] = False
    edit.form.submit()

    assert '>10<' in client.get(
        '/elections-part/elections/superregion/region-1/party-strengths'
    )
    data = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-data'
    ).json
    assert data['results'][0]['value']['back'] == 16.67
    data = client.get(
        '/elections-part/elections/superregion/region-1/json'
    ).json
    assert data['parties']['2']['2018']['voters_count']['total'] == 151

    # translations
    client.get('/locale/fr_CH')
    parties = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-data'
    ).json
    assert parties['groups'] == ['BDP', 'Le Centre', 'FDP']
    results = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths'
    ).text
    assert 'Le Centre' in results
    assert 'PDC' in results
    assert 'BDP' in results

    # with horizontal_party_strengths
    data = client.get(
        '/elections-part/elections/superregion/region-1/party-strengths-data'
        '?horizontal=True'
    ).json
    assert data['results'][0]['text'] == 'Le Centre 2022'
    assert data['results'][0]['value'] == 50.0
    assert data['results'][0]['percentage'] == True


def test_view_election_compound_part_statistics(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, canton='bl')

    statistics = client.get(
        '/elections-part/elections/superregion/region-1/statistics'
    )
    assert "Allschwil" in statistics
    assert "Noch nicht ausgezählt" in statistics

    assert "Gewählte Kandidierende" in statistics
    assert "männlich"
    assert ">42<" in statistics


def test_view_election_compound_part_json(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, canton='bl')

    response = client.get(
        '/elections-part/elections/superregion/region-1/json'
    )
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    data = response.json
    assert data['completed'] == False
    assert data['date'] == '2022-01-01'
    assert data['districts'] == [
        {
            'mandates': {'allocated': 0, 'total': 5},
            'name': 'Allschwil',
            'progress': {'counted': 1, 'total': 2}
        }
    ]
    assert data['elected_candidates'] == [
        {
            'district': 'Allschwil',
            'family_name': 'Sieger',
            'first_name': 'Hans',
            'list': 'FDP',
            'party': ''
        }
    ]
    assert data['candidate_statistics'] == {
        'male': {'age': 42, 'count': 1},
        'total': {'age': 42, 'count': 1}
    }
    assert data['elections']
    assert data['last_modified']
    assert data['mandates'] == {'allocated': 0, 'total': 5}
    assert data['progress'] == {'counted': 0, 'total': 1}
    assert data['title'] == {'de_CH': 'Elections Region 1'}
    assert data['type'] == 'election_compound_part'
    assert data['url']


def test_view_election_compound_part_summary(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)

    with freeze_time("2022-01-01 12:00"):
        upload_election_compound(client, canton='bl')

        response = client.get(
            '/elections-part/elections/superregion/region-1/summary'
        )
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.json == {
            'completed': False,
            'date': '2022-01-01',
            'domain': 'superregion',
            'elected': [['Hans', 'Sieger']],
            'elections': [
                'http://localhost/election/regional-election-b'
            ],
            'last_modified': '2022-01-01T12:00:00+00:00',
            'progress': {'counted': 0, 'total': 1},
            'title': {'de_CH': 'Elections Region 1'},
            'type': 'election_compound_part',
            'url': (
                'http://localhost/elections-part/elections/superregion/'
                'region-1'
            )
        }


def test_views_election_compound_embedded_tables(
    election_day_app_bl: TestApp
) -> None:
    client = Client(election_day_app_bl)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_election_compound(client, canton='bl')
    for tab_name in ElectionCompoundPartLayout.tabs_with_embedded_tables:
        client.get(
            f'/elections-part/elections/superregion/region-1/{tab_name}-table'
        )
