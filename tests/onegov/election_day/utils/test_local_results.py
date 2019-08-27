from datetime import date
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from onegov.election_day.utils import add_local_results


def test_add_local_results_simple(session):
    target = ArchivedResult()

    be = Canton(name='BE', canton='be')
    bern = Municipality(name='Bern', municipality='351')

    # wrong principal domain
    add_local_results(ArchivedResult(), target, be, session)
    assert not target.local

    # wrong type
    add_local_results(ArchivedResult(type='election'), target, bern, session)
    assert not target.local

    # missing ID
    add_local_results(ArchivedResult(type='vote'), target, bern, session)
    assert not target.local

    # no vote
    source = ArchivedResult(type='vote', external_id='id')
    add_local_results(source, target, bern, session)
    assert not target.local

    # no proposal
    session.add(Vote(title="Vote", domain='federation', date=date(2011, 1, 1)))
    session.flush()
    vote = session.query(Vote).one()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # no results
    vote.ballots.append(Ballot(type="proposal"))
    session.flush()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # not yet counted
    vote.proposal.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=False, yeas=1000, nays=3000, empty=0, invalid=0
        )
    )
    session.flush()
    proposal = session.query(BallotResult).one()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # simple vote
    proposal.counted = True

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert target.local
    assert target.local_answer == 'rejected'
    assert target.local_yeas_percentage == 25.0
    assert target.local_nays_percentage == 75.0

    proposal.yeas = 7000

    add_local_results(source, target, bern, session)
    assert target.local
    assert target.local_answer == 'accepted'
    assert target.local_yeas_percentage == 70.0
    assert target.local_nays_percentage == 30.0


def test_add_local_results_complex(session):
    target = ArchivedResult()

    be = Canton(name='BE', canton='be')
    bern = Municipality(name='Bern', municipality='351')

    # wrong principal domain
    add_local_results(ArchivedResult(), target, be, session)
    assert not target.local

    # wrong type
    add_local_results(ArchivedResult(type='election'), target, bern, session)
    assert not target.local

    # missing ID
    add_local_results(ArchivedResult(type='vote'), target, bern, session)
    assert not target.local

    # no vote
    source = ArchivedResult(type='vote', external_id='id')
    add_local_results(source, target, bern, session)
    assert not target.local

    # no proposal
    session.add(
        ComplexVote(title="Vote", domain='federation', date=date(2011, 1, 1))
    )
    session.flush()
    vote = session.query(ComplexVote).one()

    # no results
    target = ArchivedResult()
    vote.ballots.append(Ballot(type="counter-proposal"))
    vote.ballots.append(Ballot(type="tie-breaker"))
    session.flush()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # not yet counted
    vote.proposal.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=True, yeas=7000, nays=3000, empty=0, invalid=0
        )
    )
    vote.counter_proposal.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=False, yeas=4000, nays=6000, empty=0, invalid=0
        )
    )
    vote.tie_breaker.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=False, yeas=2000, nays=8000, empty=0, invalid=0
        )
    )
    session.flush()
    proposal = vote.proposal.results.one()
    counter = vote.counter_proposal.results.one()
    tie = vote.tie_breaker.results.one()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # complex vote
    counter.counted = True
    tie.counted = True

    # p: y, c: n, t:p
    add_local_results(source, target, bern, session)
    assert target.local
    assert target.local_answer == 'proposal'
    assert target.local_yeas_percentage == 70.0
    assert target.local_nays_percentage == 30.0

    # p: y, c: y, t:c
    counter.yeas = 9000
    counter.nays = 1000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'counter-proposal'
    assert target.local_yeas_percentage == 90.0
    assert target.local_nays_percentage == 10.0

    # p: y, c: y, t:p
    tie.yeas = 8000
    tie.nays = 2000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'proposal'
    assert target.local_yeas_percentage == 70.0
    assert target.local_nays_percentage == 30.0

    # p: n, c: y, t:p
    proposal.yeas = 3000
    proposal.nays = 7000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'counter-proposal'
    assert target.local_yeas_percentage == 90.0
    assert target.local_nays_percentage == 10.0

    # p: n, c: n, t:p
    counter.yeas = 1000
    counter.nays = 9000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'rejected'
    assert target.local_yeas_percentage == 30.0
    assert target.local_nays_percentage == 70.0
