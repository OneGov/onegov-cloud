from datetime import date
from freezegun import freeze_time
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
    assert layout.title('proposal-entities') == '__entities (Proposal)'
    assert layout.title('proposal-districts') == '__districts (Proposal)'
    assert layout.title('counter-proposal-entities') == \
        '__entities (Counter Proposal)'
    assert layout.title('counter-proposal-districts') == \
        '__districts (Counter Proposal)'
    assert layout.title('tie-breaker-entities') == '__entities (Tie-Breaker)'
    assert layout.title('tie-breaker-districts') == '__districts (Tie-Breaker)'
    assert layout.title('data') == 'Downloads'

    layout = VoteLayout(Vote(), DummyRequest())
    assert layout.type == 'simple'
    assert layout.main_view == 'Vote/entities'
    assert layout.ballot.type == 'proposal'
    assert list(layout.menu) == []

    layout = VoteLayout(
        ComplexVote(), DummyRequest(), tab='counter-proposal-entities'
    )
    assert layout.type == 'complex'
    assert layout.main_view == 'ComplexVote/proposal-entities'
    assert layout.ballot.type == 'counter-proposal'
    assert list(layout.menu) == []

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
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-__entities-proposal.svg'

        layout = VoteLayout(vote, request, 'proposal-districts')
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-__districts-proposal.svg'

        layout = VoteLayout(vote, request, 'counter-proposal-entities')
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hc}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-__entities-counter-proposal.svg'

        layout = VoteLayout(vote, request, 'counter-proposal-districts')
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hc}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-__districts-counter-proposal.svg'

        layout = VoteLayout(vote, request, 'tie-breaker-entities')
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{ht}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-__entities-tie-breaker.svg'

        layout = VoteLayout(vote, request, 'tie-breaker-districts')
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{ht}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-__districts-tie-breaker.svg'
