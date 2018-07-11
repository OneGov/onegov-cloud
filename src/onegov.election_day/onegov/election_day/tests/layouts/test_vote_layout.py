from datetime import date
from freezegun import freeze_time
from onegov.ballot import BallotResult
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.tests.common import DummyRequest
from unittest.mock import Mock


def test_vote_layout(session):
    layout = VoteLayout(Vote(), DummyRequest())

    assert layout.all_tabs == (
        'entities',
        'districts',
        'proposal-entities',
        'proposal-districts',
        'counter-proposal-entities',
        'counter-proposal-districts',
        'tie-breaker-entities',
        'tie-breaker-districts',
        'data'
    )

    assert layout.title('undefined') == ''
    assert layout.title('entities') == '__entities'
    assert layout.title('districts') == '__districts'
    assert layout.title('proposal-entities') == 'Proposal'
    assert layout.title('proposal-districts') == 'Proposal'
    assert layout.title('counter-proposal-entities') == 'Counter Proposal'
    assert layout.title('counter-proposal-districts') == 'Counter Proposal'
    assert layout.title('tie-breaker-entities') == 'Tie-Breaker'
    assert layout.title('tie-breaker-districts') == 'Tie-Breaker'
    assert layout.title('data') == 'Downloads'

    assert layout.subtitle('undefined') == ''
    assert layout.subtitle('entities') == ''
    assert layout.subtitle('districts') == ''
    assert layout.subtitle('proposal-entities') == ''
    assert layout.subtitle('proposal-districts') == '__districts'
    assert layout.subtitle('counter-proposal-entities') == ''
    assert layout.subtitle('counter-proposal-districts') == '__districts'
    assert layout.subtitle('tie-breaker-entities') == ''
    assert layout.subtitle('tie-breaker-districts') == '__districts'
    assert layout.subtitle('data') == ''

    layout.has_districts = True
    assert layout.subtitle('proposal-entities') == '__entities'
    assert layout.subtitle('counter-proposal-entities') == '__entities'
    assert layout.subtitle('tie-breaker-entities') == '__entities'

    layout = VoteLayout(Vote(), DummyRequest())
    assert layout.type == 'simple'
    assert layout.main_view == 'Vote/entities'
    assert layout.ballot.type == 'proposal'

    layout = VoteLayout(
        ComplexVote(), DummyRequest(), tab='counter-proposal-entities'
    )
    assert layout.type == 'complex'
    assert layout.main_view == 'ComplexVote/proposal-entities'
    assert layout.ballot.type == 'counter-proposal'

    with freeze_time("2014-01-01 12:00"):
        vote = ComplexVote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        assert all((vote.proposal, vote.counter_proposal, vote.tie_breaker))
        session.add(vote)
        session.flush()

        ts = '1388577600'
        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        hp = vote.proposal.id
        hc = vote.counter_proposal.id
        ht = vote.tie_breaker.id

        request = DummyRequest()
        request.app.filestorage = Mock()

        layout = VoteLayout(vote, request)
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-__entities.svg'

        layout = VoteLayout(vote, request, 'districts')
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-__districts.svg'

        layout = VoteLayout(vote, request, 'proposal-entities')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-proposal-__entities.svg'

        layout = VoteLayout(vote, request, 'proposal-districts')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-proposal-__districts.svg'

        layout = VoteLayout(vote, request, 'counter-proposal-entities')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hc}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-counter-proposal-__entities.svg'

        layout = VoteLayout(vote, request, 'counter-proposal-districts')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hc}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-counter-proposal-__districts.svg'

        layout = VoteLayout(vote, request, 'tie-breaker-entities')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{ht}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-tie-breaker-__entities.svg'

        layout = VoteLayout(vote, request, 'tie-breaker-districts')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{ht}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-tie-breaker-__districts.svg'


def test_vote_layout_menu(session):
    vote = Vote(title='Vote', date=date(2000, 1, 1), domain='federation')
    session.add(vote)
    session.flush()

    request = DummyRequest()
    assert VoteLayout(vote, request).menu == []
    assert VoteLayout(vote, request, 'data').menu == []

    vote.proposal.results.append(
        BallotResult(entity_id='1', name=1, counted=True)
    )
    assert VoteLayout(vote, request).menu == [
        ('__entities', 'Vote/entities', True, []),
        ('Downloads', 'Vote/data', False, [])
    ]
    assert VoteLayout(vote, request, 'data').menu == [
        ('__entities', 'Vote/entities', False, []),
        ('Downloads', 'Vote/data', True, [])
    ]

    request.app.principal.has_districts = True
    assert VoteLayout(vote, request).menu == [
        ('__entities', 'Vote/entities', True, []),
        ('__districts', 'Vote/districts', False, []),
        ('Downloads', 'Vote/data', False, [])
    ]


def test_vote_layout_menu_complex(session):
    vote = ComplexVote(
        title='Vote', date=date(2000, 1, 1), domain='federation'
    )
    session.add(vote)
    session.flush()

    request = DummyRequest()
    assert VoteLayout(vote, request).menu == []
    assert VoteLayout(vote, request, 'data').menu == []

    vote.proposal.results.append(
        BallotResult(entity_id='1', name=1, counted=True)
    )
    assert VoteLayout(vote, request).menu == [
        ('Proposal', 'ComplexVote/proposal-entities', False, []),
        (
            'Counter Proposal',
            'ComplexVote/counter-proposal-entities',
            False,
            []
        ),
        ('Tie-Breaker', 'ComplexVote/tie-breaker-entities', False, []),
        ('Downloads', 'ComplexVote/data', False, [])
    ]
    assert VoteLayout(vote, request, 'data').menu == [
        ('Proposal', 'ComplexVote/proposal-entities', False, []),
        (
            'Counter Proposal',
            'ComplexVote/counter-proposal-entities',
            False,
            []
        ),
        ('Tie-Breaker', 'ComplexVote/tie-breaker-entities', False, []),
        ('Downloads', 'ComplexVote/data', True, [])
    ]

    request.app.principal.has_districts = True
    assert VoteLayout(vote, request).menu == [
        ('Proposal', '', False, [
            ('__entities', 'ComplexVote/proposal-entities', False, []),
            ('__districts', 'ComplexVote/proposal-districts', False, [])
        ]),
        ('Counter Proposal', '', False, [
            ('__entities', 'ComplexVote/counter-proposal-entities', False, []),
            (
                '__districts',
                'ComplexVote/counter-proposal-districts',
                False,
                []
            )
        ]),
        ('Tie-Breaker', '', False, [
            ('__entities', 'ComplexVote/tie-breaker-entities', False, []),
            ('__districts', 'ComplexVote/tie-breaker-districts', False, [])
        ]),
        ('Downloads', 'ComplexVote/data', False, [])
    ]
