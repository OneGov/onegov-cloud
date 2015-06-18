from datetime import date
from onegov.ballot import Ballot, BallotResult, Vote


def test_create_all_models(session):
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(vote)
    session.flush()

    ballot = Ballot(
        type='proposal',
        vote_id=vote.id
    )

    session.add(ballot)
    session.flush()

    ballot_result = BallotResult(
        group='ZG/Rotkreuz',
        counted=True,
        yays=4982,
        nays=4452,
        empty=500,
        invalid=66,
        ballot_id=ballot.id
    )

    session.add(ballot_result)
    session.flush()


def test_vote_id_generation(session):
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(vote)
    session.flush()

    assert vote.id == 'universal-healthcare'


def test_ballot_answer_simple(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )

    session.add(vote)
    session.flush()

    ballot = Ballot(
        type='proposal',
        vote_id=vote.id
    )

    ballot.results.extend([
        BallotResult(
            group='Ort A',
            counted=True,
            yays=100,
            nays=50
        ),
        BallotResult(
            group='Ort B',
            counted=False,
            yays=100,
            nays=50
        )
    ])

    session.add(ballot)
    session.flush()

    # not all results are counted yet
    assert vote.answer is None

    for result in ballot.results:
        result.counted = True

    assert vote.answer == 'accepted'

    # if there are as many nays as yays, we default to 'rejected' - in reality
    # this is very unlikely to happen
    for result in ballot.results:
        result.nays = 100

    assert vote.answer == 'rejected'


def test_ballot_answer_proposal_wins(session):
    vote = Vote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(group='x', yays=100, nays=0, counted=True))
    vote.counter_proposal.results.append(
        BallotResult(group='x', yays=0, nays=100, counted=True))
    vote.tie_breaker.results.append(
        BallotResult(group='x', yays=0, nays=0, counted=True))

    assert vote.answer == 'proposal'


def test_ballot_answer_counter_proposal_wins(session):
    vote = Vote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(group='x', yays=0, nays=100, counted=True))
    vote.counter_proposal.results.append(
        BallotResult(group='x', yays=100, nays=0, counted=True))
    vote.tie_breaker.results.append(
        BallotResult(group='x', yays=0, nays=0, counted=True))

    assert vote.answer == 'counter-proposal'


def test_ballot_answer_counter_tie_breaker_decides(session):
    vote = Vote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(group='x', yays=100, nays=0, counted=True))
    vote.counter_proposal.results.append(
        BallotResult(group='x', yays=100, nays=0, counted=True))
    vote.tie_breaker.results.append(
        BallotResult(group='x', yays=100, nays=0, counted=True))

    assert vote.answer == 'proposal'

    vote.tie_breaker.results[0].yays = 0
    vote.tie_breaker.results[0].nays = 100

    assert vote.answer == 'counter-proposal'


def test_ballot_answer_nobody_wins(session):
    vote = Vote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(group='x', yays=0, nays=100, counted=True))
    vote.counter_proposal.results.append(
        BallotResult(group='x', yays=0, nays=100, counted=True))
    vote.tie_breaker.results.append(
        BallotResult(group='x', yays=100, nays=0, counted=True))

    assert vote.answer == 'rejected'


def test_progress(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(group='1', counted=True)
    )
    vote.proposal.results.append(
        BallotResult(group='2', counted=True)
    )
    vote.proposal.results.append(
        BallotResult(group='3', counted=False)
    )

    assert vote.progress == (2, 3)
    assert vote.proposal.progress == (2, 3)


def test_turnout(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(group='1', counted=True, elegible_voters=100, yays=10)
    )

    session.flush()

    assert vote.turnout == 10
    assert vote.proposal.turnout == 10


def test_ballot_results_aggregation(session):
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(vote)
    session.flush()

    ballot = Ballot(
        type='proposal',
        vote_id=vote.id
    )

    ballot.results.extend([
        BallotResult(
            group='ZG/Rotkreuz',
            counted=True,
            yays=507,
            nays=69,
            empty=14,
            invalid=5
        ),
        BallotResult(
            group='ZG/Menzingen',
            counted=True,
            yays=309,
            nays=28,
            empty=5,
            invalid=0
        )
    ])

    session.add(ballot)
    session.flush()

    assert ballot.yays == 309 + 507
    assert ballot.nays == 69 + 28
    assert ballot.empty == 14 + 5
    assert ballot.invalid == 5 + 0
    assert ballot.cast_ballots == 309 + 507 + 69 + 28 + 14 + 5 + 5 + 0
    assert ballot.accepted is True
    assert ballot.counted is True
    assert round(ballot.yays_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    session.query(Ballot.yays).first() == (309 + 507, )
    session.query(Ballot.nays).first() == (69 + 28, )
    session.query(Ballot.empty).first() == (14 + 5, )
    session.query(Ballot.invalid).first() == (5 + 0, )
    session.query(Ballot.accepted).first() == (True, )
    session.query(Ballot.counted).first() == (True, )
    session.query(Ballot.cast_ballots).first() == (
        309 + 507 + 69 + 28 + 14 + 5 + 5 + 0, )
    round(session.query(Ballot.yays_percentage).first()[0], 2) == 89.38
    round(session.query(Ballot.nays_percentage).first()[0], 2) == 10.62

    ballot = session.query(Ballot).one()
    ballot.results.append(
        BallotResult(
            group='ZG/Baar',
            counted=False
        ),
    )
    session.flush()

    assert ballot.yays == 309 + 507
    assert ballot.nays == 69 + 28
    assert ballot.empty == 14 + 5
    assert ballot.invalid == 5 + 0
    assert ballot.cast_ballots == 309 + 507 + 69 + 28 + 14 + 5 + 5 + 0
    assert ballot.accepted is None
    assert ballot.counted is False
    assert round(ballot.yays_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    session.query(Ballot.yays).first() == (309 + 507, )
    session.query(Ballot.nays).first() == (69 + 28, )
    session.query(Ballot.empty).first() == (14 + 5, )
    session.query(Ballot.invalid).first() == (5 + 0, )
    session.query(Ballot.accepted).first() == (None, )
    session.query(Ballot.counted).first() == (False, )
    session.query(Ballot.cast_ballots).first() == (
        309 + 507 + 69 + 28 + 14 + 5 + 5 + 0, )
    round(session.query(Ballot.yays_percentage).first()[0], 2) == 89.38
    round(session.query(Ballot.nays_percentage).first()[0], 2) == 10.62

    # mark as counted, but don't change any results from 0
    ballot.results[-1].counted = True
    session.flush()

    assert ballot.yays == 309 + 507
    assert ballot.nays == 69 + 28
    assert ballot.empty == 14 + 5
    assert ballot.invalid == 5 + 0
    assert ballot.cast_ballots == 309 + 507 + 69 + 28 + 14 + 5 + 5 + 0
    assert ballot.accepted is True
    assert ballot.counted is True
    assert round(ballot.yays_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    session.query(Ballot.yays).first() == (309 + 507, )
    session.query(Ballot.nays).first() == (69 + 28, )
    session.query(Ballot.empty).first() == (14 + 5, )
    session.query(Ballot.invalid).first() == (5 + 0, )
    session.query(Ballot.accepted).first() == (True, )
    session.query(Ballot.counted).first() == (True, )
    session.query(Ballot.cast_ballots).first() == (
        309 + 507 + 69 + 28 + 14 + 5 + 5 + 0, )
    round(session.query(Ballot.yays_percentage).first()[0], 2) == 89.38
    round(session.query(Ballot.nays_percentage).first()[0], 2) == 10.62
