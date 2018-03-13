from datetime import date
from freezegun import freeze_time
from onegov.ballot import Ballot
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.tests import DummyRequest
from unittest.mock import Mock


def test_vote_layout(session):
    layout = VoteLayout(Vote(), DummyRequest())

    assert layout.title() == 'Proposal'
    assert layout.title('undefined') == ''
    assert layout.title('proposal') == 'Proposal'
    assert layout.title('counter-proposal') == 'Counter Proposal'
    assert layout.title('tie-breaker') == 'Tie-Breaker'
    assert layout.title('data') == 'Downloads'

    assert list(layout.menu) == []

    with freeze_time("2014-01-01 12:00"):
        vote = ComplexVote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        proposal = Ballot(type="proposal")
        vote.ballots.append(proposal)
        counter = Ballot(type="counter-proposal")
        vote.ballots.append(counter)
        tie = Ballot(type="tie-breaker")
        vote.ballots.append(tie)
        session.add(vote)
        session.flush()

        ts = '1388577600'
        vh = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'

        request = DummyRequest()
        request.app.filestorage = Mock()

        layout = VoteLayout(vote, request)
        assert layout.pdf_path == 'pdf/vote-{}.{}.de.pdf'.format(vh, ts)
        assert layout.svg_path == 'svg/ballot-{}.{}.map.de.svg'.format(
            proposal.id, ts
        )
        assert layout.svg_link == 'Ballot/svg'
        assert layout.svg_name == 'vote-proposal.svg'

        layout = VoteLayout(vote, request, 'counter-proposal')
        assert layout.pdf_path == 'pdf/vote-{}.{}.de.pdf'.format(vh, ts)
        assert layout.svg_path == 'svg/ballot-{}.{}.map.de.svg'.format(
            counter.id, ts
        )
        assert layout.svg_link == 'Ballot/svg'
        assert layout.svg_name == 'vote-counter-proposal.svg'

        layout = VoteLayout(vote, request, 'tie-breaker')
        assert layout.pdf_path == 'pdf/vote-{}.{}.de.pdf'.format(vh, ts)
        assert layout.svg_path == 'svg/ballot-{}.{}.map.de.svg'.format(
            tie.id, ts
        )
        assert layout.svg_link == 'Ballot/svg'
        assert layout.svg_name == 'vote-tie-breaker.svg'
