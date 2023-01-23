from datetime import date
from freezegun import freeze_time
from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.ballot import ElectionRelationship
from onegov.ballot import ElectionResult
from onegov.ballot import ListConnection
from onegov.ballot import PanachageResult
from onegov.ballot import PartyResult
from onegov.ballot import ProporzElection
from onegov.election_day.layouts import ElectionLayout
from tests.onegov.election_day.common import DummyRequest
from unittest.mock import Mock
import pytest


def test_election_layout_general(session):
    majorz = Election(
        title='Majorz Election',
        domain='canton',
        date=date(2019, 1, 1)
    )
    proporz = ProporzElection(
        title='Proporz Election',
        domain='canton',
        date=date(2019, 1, 1)
    )
    session.add(majorz)
    session.add(proporz)
    session.flush()

    layout = ElectionLayout(majorz, DummyRequest())
    assert layout.all_tabs == (
        'lists',
        'list-by-entity',
        'list-by-district',
        'connections',
        'lists-panachage',
        'candidates',
        'candidate-by-entity',
        'candidate-by-district',
        'party-strengths',
        'parties-panachage',
        'statistics',
        'data'
    )

    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('lists') == 'Lists'
    assert layout.title('list-by-entity') == 'Lists'
    assert layout.title('list-by-district') == 'Lists'
    assert layout.title('connections') == 'Lists'
    assert layout.title('lists-panachage') == 'Lists'
    assert layout.title('candidates') == 'Candidates'
    assert layout.title('candidate-by-entity') == 'Candidates'
    assert layout.title('candidate-by-district') == 'Candidates'
    assert layout.title('party-strengths') == 'Parties'
    assert layout.title('parties-panachage') == 'Parties'
    assert layout.title('statistics') == 'Election statistics'
    assert layout.title('data') == 'Downloads'

    assert layout.subtitle() == ''
    assert layout.subtitle('undefined') == ''
    assert layout.subtitle('lists') == ''
    assert layout.subtitle('list-by-entity') == '__entities'
    assert layout.subtitle('list-by-district') == '__districts'
    assert layout.subtitle('connections') == 'List connections'
    assert layout.subtitle('lists-panachage') == 'Panachage'
    assert layout.subtitle('candidates') == ''
    assert layout.subtitle('candidate-by-entity') == '__entities'
    assert layout.subtitle('candidate-by-district') == '__districts'
    assert layout.subtitle('party-strengths') == 'Party strengths'
    assert layout.subtitle('parties-panachage') == 'Panachage'
    assert layout.subtitle('statistics') == ''
    assert layout.subtitle('data') == ''

    assert layout.majorz
    assert not layout.proporz
    assert layout.main_view == 'Election/candidates'
    assert not layout.tacit
    assert not layout.has_party_results

    layout = ElectionLayout(proporz, DummyRequest())
    assert not layout.majorz
    assert layout.proporz
    assert layout.main_view == 'ProporzElection/lists'
    assert not layout.tacit
    assert not layout.has_party_results

    majorz.tacit = True
    layout = ElectionLayout(majorz, DummyRequest())
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
        assert layout.svg_path == f'svg/election-{ts}.None.de.svg'
        assert layout.svg_link == 'Election/None-svg'
        assert layout.svg_name == 'election.svg'

        layout = ElectionLayout(election, request, 'lists')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.lists.de.svg'
        assert layout.svg_link == 'Election/lists-svg'
        assert layout.svg_name == 'election-lists.svg'

        layout = ElectionLayout(election, request, 'candidates')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.candidates.de.svg'
        assert layout.svg_link == 'Election/candidates-svg'
        assert layout.svg_name == 'election-candidates.svg'

        layout = ElectionLayout(election, request, 'connections')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.connections.de.svg'
        assert layout.svg_link == 'Election/connections-svg'
        assert layout.svg_name == 'election-lists-list-connections.svg'

        layout = ElectionLayout(election, request, 'party-strengths')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.party-strengths.de.svg'
        assert layout.svg_link == 'Election/party-strengths-svg'
        assert layout.svg_name == 'election-parties-party-strengths.svg'

        layout = ElectionLayout(election, request, 'parties-panachage')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert (
            layout.svg_path == f'svg/election-{ts}.parties-panachage.de.svg'
        )
        assert layout.svg_link == 'Election/parties-panachage-svg'
        assert layout.svg_name == 'election-parties-panachage.svg'

        layout = ElectionLayout(election, request, 'lists-panachage')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.lists-panachage.de.svg'
        assert layout.svg_link == 'Election/lists-panachage-svg'
        assert layout.svg_name == 'election-lists-panachage.svg'

    with freeze_time("2014-01-01 13:00"):
        second_election = Election(
            title="Second Election",
            domain='federation',
            type='proporz',
            date=date(2011, 1, 1),
        )
        session.add(second_election)
        session.flush()

        relationship = ElectionRelationship(
            source_id=election.id,
            target_id=second_election.id
        )
        session.add(relationship)
        session.flush()

        assert ElectionLayout(election, request).related_elections == [
            ('Second Election', 'Election/second-election')
        ]
        assert ElectionLayout(second_election, request).related_elections == []

    proporz.party_results.append(
        PartyResult(
            year=2017,
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'de_CH': 'A'},
            party_id='1'
        )
    )
    assert ElectionLayout(proporz, DummyRequest()).has_party_results


def test_election_layout_menu_majorz(session):
    election = Election(
        title='Vote', date=date(2000, 1, 1), domain='federation'
    )
    session.add(election)
    session.flush()

    request = DummyRequest()
    assert ElectionLayout(election, request).menu == []
    assert ElectionLayout(election, request, 'data').menu == []

    election.results.append(
        ElectionResult(
            name='1',
            entity_id=1,
            counted=True,
            eligible_voters=500,
        )
    )
    election.candidates.append(
        Candidate(
            candidate_id='1',
            family_name="1",
            first_name="1",
            elected=False
        )
    )
    assert ElectionLayout(election, request).menu == [
        ('Candidates', '', False, [
            ('Candidates', 'Election/candidates', False, []),
            ('__entities', 'Election/candidate-by-entity', False, [])
        ]),
        ('Election statistics', 'Election/statistics', False, []),
        ('Downloads', 'Election/data', False, [])
    ]
    assert ElectionLayout(election, request, 'data').menu == [
        ('Candidates', '', False, [
            ('Candidates', 'Election/candidates', False, []),
            ('__entities', 'Election/candidate-by-entity', False, [])
        ]),
        ('Election statistics', 'Election/statistics', False, []),
        ('Downloads', 'Election/data', True, [])
    ]
    assert ElectionLayout(election, request, 'candidate-by-entity').menu == [
        ('Candidates', '', True, [
            ('Candidates', 'Election/candidates', False, []),
            ('__entities', 'Election/candidate-by-entity', True, [])
        ]),
        ('Election statistics', 'Election/statistics', False, []),
        ('Downloads', 'Election/data', False, [])
    ]

    request.app.principal._is_year_available = False
    request.app.principal.has_districts = False
    assert ElectionLayout(election, request).menu == [
        ('Candidates', 'Election/candidates', False, []),
        ('Election statistics', 'Election/statistics', False, []),
        ('Downloads', 'Election/data', False, [])
    ]

    request.app.principal._is_year_available = False
    request.app.principal.has_districts = True
    assert ElectionLayout(election, request).menu == [
        ('Candidates', 'Election/candidates', False, []),
        ('Election statistics', 'Election/statistics', False, []),
        ('Downloads', 'Election/data', False, [])
    ]

    request.app.principal._is_year_available = True
    request.app.principal.has_districts = True
    assert ElectionLayout(election, request).menu == [
        ('Candidates', '', False, [
            ('Candidates', 'Election/candidates', False, []),
            ('__entities', 'Election/candidate-by-entity', False, []),
            ('__districts', 'Election/candidate-by-district', False, [])
        ]),
        ('Election statistics', 'Election/statistics', False, []),
        ('Downloads', 'Election/data', False, [])
    ]


def test_election_layout_menu_proporz(session):
    election = ProporzElection(
        title='Vote', date=date(2000, 1, 1), domain='federation'
    )
    session.add(election)
    session.flush()

    request = DummyRequest()
    assert ElectionLayout(election, request).menu == []
    assert ElectionLayout(election, request, 'data').menu == []

    election.results.append(
        ElectionResult(
            name='1',
            entity_id=1,
            counted=True,
            eligible_voters=500,
        )
    )
    election.candidates.append(
        Candidate(
            candidate_id='1',
            family_name="1",
            first_name="1",
            elected=False
        )
    )
    assert ElectionLayout(election, request).menu == [
        ('Lists', '', False, [
            ('Lists', 'ProporzElection/lists', False, []),
            ('__entities', 'ProporzElection/list-by-entity', False, [])
        ]),
        ('Candidates', '', False, [
            ('Candidates', 'ProporzElection/candidates', False, []),
            ('__entities', 'ProporzElection/candidate-by-entity', False, [])
        ]),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', False, [])
    ]
    assert ElectionLayout(election, request, 'data').menu == [
        ('Lists', '', False, [
            ('Lists', 'ProporzElection/lists', False, []),
            ('__entities', 'ProporzElection/list-by-entity', False, [])
        ]),
        ('Candidates', '', False, [
            ('Candidates', 'ProporzElection/candidates', False, []),
            ('__entities', 'ProporzElection/candidate-by-entity', False, [])
        ]),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', True, [])
    ]
    assert ElectionLayout(election, request, 'candidate-by-entity').menu == [
        ('Lists', '', False, [
            ('Lists', 'ProporzElection/lists', False, []),
            ('__entities', 'ProporzElection/list-by-entity', False, [])
        ]),
        ('Candidates', '', True, [
            ('Candidates', 'ProporzElection/candidates', False, []),
            ('__entities', 'ProporzElection/candidate-by-entity', True, [])
        ]),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', False, [])
    ]

    request.app.principal._is_year_available = False
    request.app.principal.has_districts = False
    assert ElectionLayout(election, request).menu == [
        ('Lists', 'ProporzElection/lists', False, []),
        ('Candidates', 'ProporzElection/candidates', False, []),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', False, [])
    ]

    request.app.principal._is_year_available = False
    request.app.principal.has_districts = True
    assert ElectionLayout(election, request).menu == [
        ('Lists', 'ProporzElection/lists', False, []),
        ('Candidates', 'ProporzElection/candidates', False, []),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', False, [])
    ]

    election.panachage_results.append(
        PanachageResult(target='t', source='t ', votes=0)
    )
    election.show_party_panachage = True
    assert ElectionLayout(election, request).menu == [
        ('Lists', 'ProporzElection/lists', False, []),
        ('Candidates', 'ProporzElection/candidates', False, []),
        ('Panachage', 'ProporzElection/parties-panachage', False, []),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', False, [])
    ]

    request.app.principal._is_year_available = True
    request.app.principal.has_districts = True
    election.party_results.append(
        PartyResult(
            year=2017,
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'de_CH': 'A'},
            party_id='1'
        )
    )
    election.list_connections.append(ListConnection(connection_id='A'))
    election.show_party_strengths = True
    assert ElectionLayout(election, request).menu == [
        ('Lists', '', False, [
            ('Lists', 'ProporzElection/lists', False, []),
            ('__entities', 'ProporzElection/list-by-entity', False, []),
            ('__districts', 'ProporzElection/list-by-district', False, []),
            ('List connections', 'ProporzElection/connections', False, [])
        ]),
        ('Candidates', '', False, [
            ('Candidates', 'ProporzElection/candidates', False, []),
            ('__entities', 'ProporzElection/candidate-by-entity', False, []),
            ('__districts', 'ProporzElection/candidate-by-district', False, [])
        ]),
        ('Parties', '', False, [
            ('Party strengths', 'ProporzElection/party-strengths', False, []),
            ('Panachage', 'ProporzElection/parties-panachage', False, [])
        ]),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', False, [])
    ]

    election.show_party_strengths = False
    election.show_party_panachage = False
    assert ElectionLayout(election, request).menu == [
        ('Lists', '', False, [
            ('Lists', 'ProporzElection/lists', False, []),
            ('__entities', 'ProporzElection/list-by-entity', False, []),
            ('__districts', 'ProporzElection/list-by-district', False, []),
            ('List connections', 'ProporzElection/connections', False, [])
        ]),
        ('Candidates', '', False, [
            ('Candidates', 'ProporzElection/candidates', False, []),
            ('__entities', 'ProporzElection/candidate-by-entity', False, []),
            ('__districts', 'ProporzElection/candidate-by-district', False, [])
        ]),
        ('Election statistics', 'ProporzElection/statistics', False, []),
        ('Downloads', 'ProporzElection/data', False, [])
    ]


@pytest.mark.parametrize('tab,expected', [
    ('lists', 'Election/lists-table'),
    ('list-by-entity', None),
    ('list-by-district', None),
    ('connections', 'Election/connections-table'),
    ('lists-panachage', None),
    ('candidates', 'Election/candidates-table'),
    ('candidate-by-entity', None),
    ('candidate-by-district', None),
    ('party-strengths', 'Election/party-strengths-table'),
    ('parties-panachage', None),
    ('statistics', 'Election/statistics-table'),
    ('data', None)
])
def test_election_layout_table_links(tab, expected):
    # Test link depending on tab
    election = Election(date=date(2100, 1, 1), domain='federation')
    layout = ElectionLayout(election, DummyRequest(), tab=tab)
    assert expected == layout.table_link()
