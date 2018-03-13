from datetime import date
from freezegun import freeze_time
from onegov.ballot import Election
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.tests import DummyRequest
from unittest.mock import Mock


def test_election_layout(session):
    layout = ElectionLayout(None, DummyRequest())

    assert layout.all_tabs == (
        'lists', 'candidates', 'connections', 'parties', 'statistics',
        'panachage', 'data'
    )

    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('lists') == 'Lists'
    assert layout.title('candidates') == 'Candidates'
    assert layout.title('connections') == 'List connections'
    assert layout.title('parties') == 'Parties'
    assert layout.title('statistics') == 'Election statistics'
    assert layout.title('data') == 'Downloads'
    assert layout.title('panachage') == 'Panachage'

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
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.None.any.svg'.format(ts)
        assert layout.svg_link == 'Election/None-svg'
        assert layout.svg_name == 'election.svg'

        layout = ElectionLayout(election, request, 'lists')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.lists.any.svg'.format(ts)
        assert layout.svg_link == 'Election/lists-svg'
        assert layout.svg_name == 'election-lists.svg'

        layout = ElectionLayout(election, request, 'candidates')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.candidates.any.svg'.format(
            ts
        )
        assert layout.svg_link == 'Election/candidates-svg'
        assert layout.svg_name == 'election-candidates.svg'

        layout = ElectionLayout(election, request, 'connections')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.connections.any.svg'.format(
            ts
        )
        assert layout.svg_link == 'Election/connections-svg'
        assert layout.svg_name == 'election-list-connections.svg'

        layout = ElectionLayout(election, request, 'panachage')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.panachage.any.svg'.format(
            ts
        )
        assert layout.svg_link == 'Election/panachage-svg'
        assert layout.svg_name == 'election-panachage.svg'

        layout = ElectionLayout(election, request, 'parties')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.parties.any.svg'.format(ts)
        assert layout.svg_link == 'Election/parties-svg'
        assert layout.svg_name == 'election-parties.svg'
