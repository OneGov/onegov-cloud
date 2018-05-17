from datetime import date
from freezegun import freeze_time
from onegov.ballot import Election
from onegov.ballot import ElectionAssociation
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.tests.common import DummyRequest
from unittest.mock import Mock


def test_election_layout(session):
    layout = ElectionLayout(None, DummyRequest())

    assert layout.all_tabs == (
        'lists',
        'candidates',
        'connections',
        'party-strengths',
        'parties-panachage',
        'statistics',
        'lists-panachage',
        'data'
    )

    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('lists') == 'Lists'
    assert layout.title('candidates') == 'Candidates'
    assert layout.title('connections') == 'List connections'
    assert layout.title('party-strengths') == 'Party strengths'
    assert layout.title('parties-panachage') == 'Panachage (parties)'
    assert layout.title('statistics') == 'Election statistics'
    assert layout.title('data') == 'Downloads'
    assert layout.title('lists-panachage') == 'Panachage (lists)'

    layout = ElectionLayout(Election(type='majorz'), DummyRequest())
    assert layout.majorz
    assert not layout.proporz
    assert layout.main_view == 'Election/candidates'
    assert list(layout.menu) == []
    assert not layout.tacit

    layout = ElectionLayout(Election(type='proporz'), DummyRequest())
    assert not layout.majorz
    assert layout.proporz
    assert layout.main_view == 'Election/lists'
    assert list(layout.menu) == []
    assert not layout.tacit

    layout = ElectionLayout(
        Election(type='majorz', tacit=True), DummyRequest()
    )
    assert layout.tacit

    with freeze_time("2014-01-01 12:00"):
        election = Election(
            title="Election",
            domain='federation',
            type='proporz',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.flush()
        ts = (
            '4b9e99d2bd5e48d9a569e5f82175d1d2ed59105f8d82a12dc51b673ff12dc1f2'
            '.1388577600'
        )

        request = DummyRequest()
        request.app.filestorage = Mock()

        layout = ElectionLayout(election, request)
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.None.any.svg'
        assert layout.svg_link == 'Election/None-svg'
        assert layout.svg_name == 'election.svg'

        layout = ElectionLayout(election, request, 'lists')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.lists.any.svg'
        assert layout.svg_link == 'Election/lists-svg'
        assert layout.svg_name == 'election-lists.svg'

        layout = ElectionLayout(election, request, 'candidates')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.candidates.any.svg'
        assert layout.svg_link == 'Election/candidates-svg'
        assert layout.svg_name == 'election-candidates.svg'

        layout = ElectionLayout(election, request, 'connections')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.connections.any.svg'
        assert layout.svg_link == 'Election/connections-svg'
        assert layout.svg_name == 'election-list-connections.svg'

        layout = ElectionLayout(election, request, 'party-strengths')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.party-strengths.any.svg'
        assert layout.svg_link == 'Election/party-strengths-svg'
        assert layout.svg_name == 'election-party-strengths.svg'

        layout = ElectionLayout(election, request, 'parties-panachage')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert (
            layout.svg_path == f'svg/election-{ts}.parties-panachage.any.svg'
        )
        assert layout.svg_link == 'Election/parties-panachage-svg'
        assert layout.svg_name == 'election-panachage-parties.svg'

        layout = ElectionLayout(election, request, 'lists-panachage')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.lists-panachage.any.svg'
        assert layout.svg_link == 'Election/lists-panachage-svg'
        assert layout.svg_name == 'election-panachage-lists.svg'

    with freeze_time("2014-01-01 13:00"):
        second_election = Election(
            title="Second Election",
            domain='federation',
            type='proporz',
            date=date(2011, 1, 1),
        )
        session.add(second_election)
        session.flush()

        association = ElectionAssociation(
            source_id=election.id,
            target_id=second_election.id
        )
        session.add(association)
        session.flush()

        assert ElectionLayout(election, request).related_elections == [
            ('Second Election', 'Election/second-election')
        ]
        assert ElectionLayout(second_election, request).related_elections == []
