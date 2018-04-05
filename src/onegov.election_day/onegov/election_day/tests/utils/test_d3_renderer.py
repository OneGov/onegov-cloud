from base64 import b64encode
from datetime import date
from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.election_day import _
from onegov.election_day.utils.d3_renderer import D3Renderer
from unittest.mock import patch, MagicMock


def test_d3_renderer_scripts(election_day_app):
    generator = D3Renderer(election_day_app)
    assert len(generator.scripts)


def test_d3_renderer_translatation(election_day_app):
    generator = D3Renderer(election_day_app)

    assert generator.translate(_('Election'), 'de_CH') == 'Wahl'
    assert generator.translate(_('Election'), 'fr_CH') == 'Election'
    assert generator.translate(_('Election'), 'it_CH') == 'Elezione'
    assert generator.translate(_('Election'), 'rm_CH') == 'Elecziun'


def test_d3_renderer_get_chart(election_day_app):
    d3 = D3Renderer(election_day_app)

    with patch('onegov.election_day.utils.d3_renderer.post',
               return_value=MagicMock(text='<svg></svg>')) as post:
        data = {'key': 'value'}
        params = {'p': '1'}

        chart = d3.get_chart('bar', 'svg', data, 1000, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 1
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'barChart'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 1000,
            'data': {'key': 'value'},
            'width': 1000
        }

        chart = d3.get_chart('grouped', 'svg', data, 800, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 2
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'groupedChart'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 800,
            'data': {'key': 'value'},
            'width': 800
        }

        chart = d3.get_chart('sankey', 'svg', data, 600, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 3
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'sankeyChart'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 600,
            'data': {'key': 'value'},
            'width': 600
        }

        chart = d3.get_chart('entities-map', 'svg', data, 400, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 4
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'entitiesMap'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 400,
            'data': {'key': 'value'},
            'width': 400
        }

        chart = d3.get_chart('districts-map', 'svg', data, 400, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 5
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'districtsMap'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 400,
            'data': {'key': 'value'},
            'width': 400
        }

        chart = d3.get_map('entities', 'svg', data, 2015, 400, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 6
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'entitiesMap'
        assert post.call_args[1]['json']['params']['width'] == 400
        assert post.call_args[1]['json']['params']['viewport_width'] == 400
        assert post.call_args[1]['json']['params']['p'] == '1'
        assert post.call_args[1]['json']['params']['data'] == data
        assert post.call_args[1]['json']['params']['mapdata']
        assert post.call_args[1]['json']['params']['canton'] == 'zg'

        chart = d3.get_map('districts', 'svg', data, 2015, 400, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 7
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'districtsMap'
        assert post.call_args[1]['json']['params']['width'] == 400
        assert post.call_args[1]['json']['params']['viewport_width'] == 400
        assert post.call_args[1]['json']['params']['p'] == '1'
        assert post.call_args[1]['json']['params']['data'] == data
        assert post.call_args[1]['json']['params']['mapdata']
        assert post.call_args[1]['json']['params']['canton'] == 'zg'

    with patch('onegov.election_day.utils.d3_renderer.post',
               return_value=MagicMock(text=b64encode('PDF'.encode()))) as post:
        data = {'key': 'value'}

        d3.get_chart('bar', 'pdf', data).read().decode() == 'PDF'
        d3.get_chart('grouped', 'pdf', data).read().decode() == 'PDF'
        d3.get_chart('sankey', 'pdf', data).read().decode() == 'PDF'
        d3.get_chart('entities-map', 'pdf', data).read().decode() == 'PDF'
        d3.get_chart('districts-map', 'pdf', data).read().decode() == 'PDF'
        d3.get_map('entities', 'pdf', data, 2015).read().decode() == 'PDF'
        d3.get_map('districts', 'pdf', data, 2015).read().decode() == 'PDF'
        assert post.call_args[0] == ('http://localhost:1337/d3/pdf',)


def test_d3_renderer_get_charts(election_day_app):
    election = Election(
        title="Election",
        domain='federation',
        date=date(2011, 1, 1),
    )
    compound = ElectionCompound(
        title="ElectionCompound",
        domain='canton',
        date=date(2011, 1, 1),
    )
    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2011, 1, 1),
    )
    vote.ballots.append(Ballot(type='proposal'))

    session = election_day_app.session()
    session.add(election)
    session.add(compound)
    session.add(vote)

    d3 = D3Renderer(election_day_app)

    assert d3.get_lists_chart(election, 'svg') is None
    assert d3.get_lists_chart(compound, 'svg') is None
    assert d3.get_lists_chart(vote, 'svg') is None
    assert d3.get_lists_chart(vote.proposal, 'svg') is None

    assert d3.get_candidates_chart(election, 'svg') is None
    assert d3.get_candidates_chart(compound, 'svg') is None
    assert d3.get_candidates_chart(vote, 'svg') is None
    assert d3.get_candidates_chart(vote.proposal, 'svg') is None

    assert d3.get_connections_chart(election, 'svg') is None
    assert d3.get_connections_chart(compound, 'svg') is None
    assert d3.get_connections_chart(vote, 'svg') is None
    assert d3.get_connections_chart(vote.proposal, 'svg') is None

    assert d3.get_party_strengths_chart(election, 'svg') is None
    assert d3.get_party_strengths_chart(compound, 'svg') is None
    assert d3.get_party_strengths_chart(vote, 'svg') is None
    assert d3.get_party_strengths_chart(vote.proposal, 'svg') is None

    assert d3.get_lists_panachage_chart(election, 'svg') is None
    assert d3.get_lists_panachage_chart(compound, 'svg') is None
    assert d3.get_lists_panachage_chart(vote, 'svg') is None
    assert d3.get_lists_panachage_chart(vote.proposal, 'svg') is None

    assert d3.get_parties_panachage_chart(election, 'svg') is None
    assert d3.get_parties_panachage_chart(compound, 'svg') is None
    assert d3.get_parties_panachage_chart(vote, 'svg') is None
    assert d3.get_parties_panachage_chart(vote.proposal, 'svg') is None

    assert d3.get_entities_map(election, 'svg') is None
    assert d3.get_entities_map(compound, 'svg') is None
    assert d3.get_entities_map(vote, 'svg') is None
    assert d3.get_entities_map(vote.proposal, 'svg') is None

    assert d3.get_districts_map(election, 'svg') is None
    assert d3.get_districts_map(compound, 'svg') is None
    assert d3.get_districts_map(vote, 'svg') is None
    assert d3.get_districts_map(vote.proposal, 'svg') is None
