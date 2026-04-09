from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.models import Ballot
from onegov.election_day.models import BallotResult
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from io import BytesIO
    from onegov.election_day.types import Status
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def test_vote(session: Session) -> None:
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    vote.proposal.title = 'Proposal'
    vote.proposal.results.append(
        BallotResult(
            district='ZG',
            name='Rotkreuz',
            counted=True,
            yeas=4982,
            nays=4452,
            empty=500,
            invalid=66,
            entity_id=1
        )
    )
    session.add(vote)
    session.flush()

    vote = session.query(Vote).one()

    assert vote.type == 'simple'
    assert vote.title == "Universal Healthcare"
    assert vote.domain == 'federation'
    assert vote.date == date(2015, 6, 14)
    assert vote.proposal
    assert vote.ballot('proposal')
    assert vote.ballot('counter-proposal')
    assert vote.ballot('tie-breaker')

    assert vote.proposal.type == 'proposal'
    assert vote.proposal.title == "Proposal"

    assert vote.proposal.results[0].district == 'ZG'
    assert vote.proposal.results[0].name == 'Rotkreuz'
    assert vote.proposal.results[0].counted is True
    assert vote.proposal.results[0].yeas == 4982
    assert vote.proposal.results[0].nays == 4452
    assert vote.proposal.results[0].empty == 500
    assert vote.proposal.results[0].invalid == 66
    assert vote.proposal.results[0].entity_id == 1


def test_complex_vote(session: Session) -> None:
    vote_ = ComplexVote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    # todo: add results, title etc
    session.add(vote_)
    session.flush()

    vote = session.query(Vote).one()
    assert isinstance(vote, ComplexVote)
    assert vote.type == 'complex'
    assert vote.title == "Universal Healthcare"
    assert vote.domain == 'federation'
    assert vote.date == date(2015, 6, 14)
    assert vote.proposal
    assert vote.counter_proposal
    assert vote.tie_breaker
    assert vote.ballot('proposal')
    assert vote.ballot('counter-proposal')
    assert vote.ballot('tie-breaker')


def test_vote_id_generation(session: Session) -> None:
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(vote)
    session.flush()
    assert vote.id == 'universal-healthcare'

    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(vote)
    session.flush()
    assert vote.id == 'universal-healthcare-1'

    vote = ComplexVote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(vote)
    session.flush()
    assert vote.id == 'universal-healthcare-2'

    vote = ComplexVote(
        title="Universal Healthcare",
        short_title="UHC",
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(vote)
    session.flush()
    assert vote.id == 'uhc'


def test_ballot_answer_simple(session: Session) -> None:
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )

    # no ballot yet
    assert vote.answer is None

    # add ballot
    vote.proposal.results.extend([
        BallotResult(
            name='Ort A',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        ),
        BallotResult(
            name='Ort B',
            counted=False,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    ])

    # not all results are counted yet
    assert vote.proposal.answer is None
    assert vote.answer is None

    # set results to counted
    for result in vote.proposal.results:
        result.counted = True
    assert vote.proposal.answer == 'accepted'
    assert vote.answer == 'accepted'

    # if there are as many nays as yeas, we default to 'rejected' - in reality
    # this is very unlikely to happen
    for result in vote.proposal.results:
        result.nays = 100

    assert vote.proposal.answer == 'rejected'
    assert vote.answer == 'rejected'


def test_ballot_nobody_voted_right(session: Session) -> None:
    vote = Vote(
        title="Should we go voting?",
        domain='federation',
        date=date(2015, 6, 18)
    )

    # if nobody casts a valid vote, the result is 100% no
    result = BallotResult(
        entity_id=10,
        name='Govikon',
        counted=True,
        yeas=0,
        nays=0,
        invalid=100,
        empty=100
    )
    vote.proposal.results.append(result)
    assert result.yeas_percentage == 0
    assert result.nays_percentage == 100.0

    # make sure this works in an aggregated fashion as well
    vote.proposal.results.append(
        BallotResult(
            entity_id=10,
            name='Govikon',
            counted=True,
            yeas=0,
            nays=0,
            invalid=100,
            empty=100
        )
    )
    assert vote.yeas_percentage == 0
    assert vote.nays_percentage == 100.0


def test_ballot_answer_proposal_wins(session: Session) -> None:
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1))

    assert vote.proposal.answer == 'accepted'
    assert vote.counter_proposal.answer == 'rejected'
    assert vote.tie_breaker.answer == 'counter-proposal'
    assert vote.answer == 'proposal'
    assert vote.yeas_percentage == 100.0
    assert vote.nays_percentage == 0


def test_ballot_answer_counter_proposal_wins(session: Session) -> None:
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    # if only the counter-proposal is accepted, the counter-proposal wins
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1))

    assert vote.proposal.answer == 'rejected'
    assert vote.counter_proposal.answer == 'accepted'
    assert vote.tie_breaker.answer == 'counter-proposal'
    assert vote.answer == 'counter-proposal'
    assert vote.yeas_percentage == 100.0
    assert vote.nays_percentage == 0


def test_ballot_answer_counter_tie_breaker_decides(session: Session) -> None:
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    # if both are accepted, the tie-breaker decides
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=70, nays=30, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=80, nays=20, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))

    assert vote.proposal.answer == 'accepted'
    assert vote.counter_proposal.answer == 'accepted'
    assert vote.tie_breaker.answer == 'proposal'
    assert vote.answer == 'proposal'
    assert vote.yeas_percentage == 70.0
    assert vote.nays_percentage == 30.0

    vote.tie_breaker.results[0].yeas = 0
    vote.tie_breaker.results[0].nays = 100

    assert vote.proposal.answer == 'accepted'
    assert vote.counter_proposal.answer == 'accepted'
    assert vote.tie_breaker.answer == 'counter-proposal'
    assert vote.answer == 'counter-proposal'
    assert vote.yeas_percentage == 80.0
    assert vote.nays_percentage == 20.0


def test_ballot_answer_nobody_wins(session: Session) -> None:
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    # if none is accepted, none wins
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))

    assert vote.proposal.answer == 'rejected'
    assert vote.counter_proposal.answer == 'rejected'
    assert vote.tie_breaker.answer == 'proposal'
    assert vote.answer == 'rejected'


def test_vote_progress(session: Session) -> None:

    def result(name: str, counted: bool) -> BallotResult:
        return BallotResult(name=name, counted=counted, entity_id=1)

    # Simple vote
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18),
    )

    assert vote.progress == (0, 0)
    assert vote.proposal.progress == (0, 0)
    assert vote.counted_entities == []

    vote.proposal.results.append(result('A', True))
    vote.proposal.results.append(result('B', True))
    vote.proposal.results.append(result('C', False))

    assert vote.progress == (2, 3)
    assert vote.proposal.progress == (2, 3)
    assert vote.counted_entities == ['A', 'B']

    # Complex vote
    vote = ComplexVote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18),
    )

    assert vote.progress == (0, 0)
    assert vote.proposal.progress == (0, 0)
    assert vote.counter_proposal.progress == (0, 0)
    assert vote.tie_breaker.progress == (0, 0)
    assert vote.counted_entities == []

    vote.proposal.results.append(result('A', True))
    vote.proposal.results.append(result('B', True))
    vote.proposal.results.append(result('C', False))
    vote.counter_proposal.results.append(result('A', True))
    vote.counter_proposal.results.append(result('B', True))
    vote.counter_proposal.results.append(result('C', False))
    vote.tie_breaker.results.append(result('A', True))
    vote.tie_breaker.results.append(result('B', True))
    vote.tie_breaker.results.append(result('C', False))

    assert vote.progress == (2, 3)
    assert vote.proposal.progress == (2, 3)
    assert vote.counter_proposal.progress == (2, 3)
    assert vote.tie_breaker.progress == (2, 3)
    assert vote.counted_entities == ['A', 'B']


def test_vote_results_by_district(session: Session) -> None:
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )
    assert vote.proposal  # create
    session.add(vote)
    session.flush()
    assert vote.proposal.results_by_district.all() == []

    vote.proposal.results.append(
        BallotResult(
            name='1', entity_id=1,
            counted=True, eligible_voters=100,
            yeas=75, nays=25
        )
    )
    session.flush()
    assert [list(r) for r in vote.proposal.results_by_district] == [
        [None, True, True, 75, 25, 75.0, 25.0, 0, 0, 100, [1]]
    ]

    vote.proposal.results.append(
        BallotResult(
            name='2', entity_id=2,
            counted=False, eligible_voters=100,
            yeas=25, nays=75
        )
    )
    session.flush()
    assert [list(r) for r in vote.proposal.results_by_district] == [
        [None, False, None, 100, 100, 50.0, 50.0, 0, 0, 200, [1, 2]]
    ]

    vote.proposal.results.append(
        BallotResult(
            name='1', entity_id=3, district='a',
            counted=True, eligible_voters=100,
            empty=1, invalid=2, yeas=10, nays=30
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='2', entity_id=4, district='a',
            counted=True, eligible_voters=200,
            empty=3, invalid=4, yeas=50, nays=10
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='3', entity_id=5, district='b',
            counted=True, eligible_voters=300,
            empty=5, invalid=6, yeas=30, nays=10
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='4', entity_id=6, district='b',
            counted=True, eligible_voters=400,
            empty=7, invalid=8, yeas=10, nays=50
        )
    )
    assert [list(r) for r in vote.proposal.results_by_district] == [
        ['a', True, True, 60, 40, 60.0, 40.0, 4, 6, 300, [3, 4]],
        ['b', True, False, 40, 60, 40.0, 60.0, 12, 14, 700, [5, 6]],
        [None, False, None, 100, 100, 50.0, 50.0, 0, 0, 200, [1, 2]]
    ]


def test_ballot_hybrid_properties(session: Session) -> None:
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(vote)
    session.flush()

    assert vote.yeas == 0
    assert vote.nays == 0
    assert vote.empty == 0
    assert vote.invalid == 0
    assert vote.eligible_voters == 0
    assert vote.expats == 0
    assert vote.cast_ballots == 0
    assert vote.turnout == 0

    assert session.query(Vote.yeas).scalar() == 0
    assert session.query(Vote.nays).scalar() == 0
    assert session.query(Vote.empty).scalar() == 0
    assert session.query(Vote.invalid).scalar() == 0
    assert session.query(Vote.eligible_voters).scalar() == 0
    assert session.query(Vote.expats).scalar() == 0
    assert session.query(Vote.cast_ballots).scalar() == 0
    assert session.query(Vote.turnout).scalar() == 0

    assert vote.proposal.yeas == 0
    assert vote.proposal.nays == 0
    assert vote.proposal.empty == 0
    assert vote.proposal.invalid == 0
    assert vote.proposal.eligible_voters == 0
    assert vote.proposal.expats == 0
    assert vote.proposal.cast_ballots == 0
    assert vote.proposal.turnout == 0
    assert vote.proposal.accepted is None
    assert vote.proposal.counted is False
    assert round(vote.proposal.yeas_percentage, 2) == 0.00
    assert round(vote.proposal.nays_percentage, 2) == 100.0

    assert session.query(Ballot.yeas).scalar() == 0
    assert session.query(Ballot.nays).scalar() == 0
    assert session.query(Ballot.empty).scalar() == 0
    assert session.query(Ballot.invalid).scalar() == 0
    assert session.query(Ballot.eligible_voters).scalar() == 0
    assert session.query(Ballot.expats).scalar() == 0
    assert session.query(Ballot.cast_ballots).scalar() == 0
    assert session.query(Ballot.turnout).scalar() == 0
    assert session.query(Ballot.accepted).scalar() is None
    assert session.query(Ballot.counted).scalar() is False
    assert session.query(Ballot.yeas_percentage).scalar() == 0.00
    assert session.query(Ballot.nays_percentage).scalar() == 100.00

    vote.proposal.results.extend([
        BallotResult(
            district='ZG',
            name='Rotkreuz',
            counted=True,
            eligible_voters=2877,
            expats=17,
            yeas=507,
            nays=69,
            empty=14,
            invalid=5,
            entity_id=1,
        ),
        BallotResult(
            district='ZG',
            name='Menzingen',
            counted=True,
            eligible_voters=1255,
            expats=1,
            yeas=309,
            nays=28,
            empty=5,
            invalid=0,
            entity_id=2,
        )
    ])

    # undo mypy narrowing
    vote = vote
    assert vote.proposal.yeas == 816
    assert vote.proposal.nays == 97
    assert vote.proposal.empty == 19
    assert vote.proposal.invalid == 5
    assert vote.proposal.eligible_voters == 4132
    assert vote.proposal.expats == 18
    assert vote.proposal.cast_ballots == 937
    assert round(vote.proposal.turnout, 2) == 22.68
    assert vote.proposal.accepted is True
    assert vote.proposal.counted is True
    assert round(vote.proposal.yeas_percentage, 2) == 89.38
    assert round(vote.proposal.nays_percentage, 2) == 10.62

    assert session.query(Ballot.yeas).scalar() == 816
    assert session.query(Ballot.nays).scalar() == 97
    assert session.query(Ballot.empty).scalar() == 19
    assert session.query(Ballot.invalid).scalar() == 5
    assert session.query(Ballot.eligible_voters).scalar() == 4132
    assert session.query(Ballot.expats).scalar() == 18
    assert session.query(Ballot.cast_ballots).scalar() == 937
    assert round(session.query(Ballot.turnout).scalar(), 2) == 22.68
    assert session.query(Ballot.accepted).scalar() is True
    assert session.query(Ballot.counted).scalar() is True
    assert round(session.query(Ballot.yeas_percentage).scalar(), 2) == 89.38
    assert round(session.query(Ballot.nays_percentage).scalar(), 2) == 10.62

    assert vote.yeas == 816
    assert vote.nays == 97
    assert vote.empty == 19
    assert vote.invalid == 5
    assert vote.eligible_voters == 4132
    assert vote.expats == 18
    assert vote.cast_ballots == 937
    assert round(vote.turnout, 2) == 22.68
    assert vote.counted is True
    assert round(vote.yeas_percentage, 2) == 89.38
    assert round(vote.nays_percentage, 2) == 10.62

    assert session.query(Vote.yeas).scalar() == 816
    assert session.query(Vote.nays).scalar() == 97
    assert session.query(Vote.empty).scalar() == 19
    assert session.query(Vote.invalid).scalar() == 5
    assert session.query(Vote.eligible_voters).scalar() == 4132
    assert session.query(Vote.expats).scalar() == 18
    assert session.query(Vote.cast_ballots).scalar() == 937
    assert round(session.query(Vote.turnout).scalar(), 2) == 22.68

    vote.proposal.results.append(
        BallotResult(
            district='ZG',
            name='Baar',
            counted=False,
            entity_id=3,
            eligible_voters=420,
            expats=10
        ),
    )

    # undo mypy narrowing
    vote = vote
    assert vote.proposal.yeas == 816
    assert vote.proposal.nays == 97
    assert vote.proposal.empty == 19
    assert vote.proposal.invalid == 5
    assert vote.proposal.eligible_voters == 4552
    assert vote.proposal.expats == 28
    assert vote.proposal.cast_ballots == 937
    assert round(vote.proposal.turnout, 2) == 20.58
    assert vote.proposal.accepted is None
    assert vote.proposal.counted is False
    assert round(vote.proposal.yeas_percentage, 2) == 89.38
    assert round(vote.proposal.nays_percentage, 2) == 10.62

    assert session.query(Ballot.yeas).scalar() == 816
    assert session.query(Ballot.nays).scalar() == 97
    assert session.query(Ballot.empty).scalar() == 19
    assert session.query(Ballot.invalid).scalar() == 5
    assert session.query(Ballot.eligible_voters).scalar() == 4552
    assert session.query(Ballot.expats).scalar() == 28
    assert session.query(Ballot.cast_ballots).scalar() == 937
    assert round(session.query(Ballot.turnout).scalar(), 2) == 20.58
    assert session.query(Ballot.accepted).scalar() is None
    assert session.query(Ballot.counted).scalar() is False
    assert round(session.query(Ballot.yeas_percentage).scalar(), 2) == 89.38
    assert round(session.query(Ballot.nays_percentage).scalar(), 2) == 10.62

    assert vote.yeas == 816
    assert vote.nays == 97
    assert vote.empty == 19
    assert vote.invalid == 5
    assert vote.eligible_voters == 4552
    assert vote.expats == 28
    assert vote.cast_ballots == 937
    assert round(vote.turnout, 2) == 20.58
    assert vote.counted is False
    assert round(vote.yeas_percentage, 2) == 89.38
    assert round(vote.nays_percentage, 2) == 10.62

    assert session.query(Vote.yeas).scalar() == 816
    assert session.query(Vote.nays).scalar() == 97
    assert session.query(Vote.empty).scalar() == 19
    assert session.query(Vote.invalid).scalar() == 5
    assert session.query(Vote.eligible_voters).scalar() == 4552
    assert session.query(Vote.expats).scalar() == 28
    assert session.query(Vote.cast_ballots).scalar() == 937
    assert round(session.query(Vote.turnout).scalar(), 2) == 20.58

    # mark as counted, but don't change any results from 0
    vote.proposal.results[2].counted = True

    # undo mypy narrowing
    vote = vote
    assert vote.proposal.yeas == 816
    assert vote.proposal.nays == 97
    assert vote.proposal.empty == 19
    assert vote.proposal.invalid == 5
    assert vote.proposal.eligible_voters == 4552
    assert vote.proposal.expats == 28
    assert vote.proposal.cast_ballots == 937
    assert round(vote.proposal.turnout, 2) == 20.58
    assert vote.proposal.accepted is True
    assert vote.proposal.counted is True
    assert round(vote.proposal.yeas_percentage, 2) == 89.38
    assert round(vote.proposal.nays_percentage, 2) == 10.62

    assert session.query(Ballot.yeas).scalar() == 816
    assert session.query(Ballot.nays).scalar() == 97
    assert session.query(Ballot.empty).scalar() == 19
    assert session.query(Ballot.invalid).scalar() == 5
    assert session.query(Ballot.eligible_voters).scalar() == 4552
    assert session.query(Ballot.expats).scalar() == 28
    assert session.query(Ballot.cast_ballots).scalar() == 937
    assert round(session.query(Ballot.turnout).scalar(), 2) == 20.58
    assert session.query(Ballot.accepted).scalar() is True
    assert session.query(Ballot.counted).scalar() is True
    assert round(session.query(Ballot.yeas_percentage).scalar(), 2) == 89.38
    assert round(session.query(Ballot.nays_percentage).scalar(), 2) == 10.62

    assert vote.yeas == 816
    assert vote.nays == 97
    assert vote.empty == 19
    assert vote.invalid == 5
    assert vote.eligible_voters == 4552
    assert vote.expats == 28
    assert vote.cast_ballots == 937
    assert round(vote.turnout, 2) == 20.58
    assert vote.counted is True
    assert round(vote.yeas_percentage, 2) == 89.38
    assert round(vote.nays_percentage, 2) == 10.62

    assert session.query(Vote.yeas).scalar() == 816
    assert session.query(Vote.nays).scalar() == 97
    assert session.query(Vote.empty).scalar() == 19
    assert session.query(Vote.invalid).scalar() == 5
    assert session.query(Vote.eligible_voters).scalar() == 4552
    assert session.query(Vote.expats).scalar() == 28
    assert session.query(Vote.cast_ballots).scalar() == 937
    assert round(session.query(Vote.turnout).scalar(), 2) == 20.58

    # Ballot Result
    ballot_result = vote.proposal.results[0]
    assert round(ballot_result.yeas_percentage, 2) == 88.02
    assert round(ballot_result.nays_percentage, 2) == 11.98
    assert ballot_result.accepted is True
    assert round(ballot_result.turnout, 2) == 20.68
    assert ballot_result.cast_ballots == 595

    assert round(
        session.query(BallotResult.yeas_percentage)
        .filter_by(entity_id=1).scalar(),
        2
    ) == 88.02
    assert round(
        session.query(BallotResult.nays_percentage)
        .filter_by(entity_id=1).scalar(),
        2
    ) == 11.98
    assert session.query(BallotResult.accepted
        ).filter_by(entity_id=1).scalar() is True
    assert round(
        session.query(BallotResult.turnout)
        .filter_by(entity_id=1).scalar(),
        2
    ) == 20.68
    assert session.query(BallotResult.cast_ballots
        ).filter_by(entity_id=1).scalar() == 595

    ballot_result.eligible_voters = 0
    assert ballot_result.turnout == 0
    assert session.query(BallotResult.turnout
        ).filter_by(entity_id=1).scalar() == 0


def test_vote_last_modified(session: Session) -> None:
    # Add vote
    with freeze_time("2001-01-01"):
        vote = Vote(
            title="Abstimmung",
            domain='federation',
            date=date(2015, 6, 18)
        )
        assert vote.last_ballot_change is None
        assert vote.last_modified is None

        session.add(vote)
        session.flush()
        # undo mypy narrowing
        vote = vote
        assert vote.last_ballot_change is None
        assert session.query(Vote.last_ballot_change).scalar() is None
        assert vote.last_modified is not None
        assert vote.last_modified.isoformat().startswith('2001')
        assert session.query(Vote.last_modified
            ).scalar().isoformat().startswith('2001')

    with freeze_time("2002-01-01"):
        vote.last_result_change = vote.timestamp()
        session.flush()
        assert vote.last_ballot_change is None
        assert session.query(Vote.last_ballot_change).scalar() is None
        assert vote.last_modified.isoformat().startswith('2002')
        assert session.query(Vote.last_modified
            ).scalar().isoformat().startswith('2002')

    with freeze_time("2003-01-01"):
        vote.domain = 'canton'
        session.flush()
        assert vote.last_ballot_change is None
        assert session.query(Vote.last_ballot_change).scalar() is None
        assert vote.last_modified.isoformat().startswith('2003')
        assert session.query(Vote.last_modified
            ).scalar().isoformat().startswith('2003')

    with freeze_time("2004-01-01"):
        vote.ballot('proposal')
        session.flush()
        # undo mypy narrowing
        vote = vote
        assert vote.last_ballot_change is not None
        assert vote.last_ballot_change.isoformat().startswith('2004')
        assert session.query(Vote.last_ballot_change
            ).scalar().isoformat().startswith('2004')
        assert vote.last_modified is not None
        assert vote.last_modified.isoformat().startswith('2004')
        assert session.query(Vote.last_modified
            ).scalar().isoformat().startswith('2004')

    with freeze_time("2005-01-01"):
        vote.proposal.title = 'Proposal'
        session.flush()
        assert vote.last_ballot_change.isoformat().startswith('2005')
        assert session.query(Vote.last_ballot_change
            ).scalar().isoformat().startswith('2005')
        assert vote.last_modified.isoformat().startswith('2005')
        assert session.query(Vote.last_modified
            ).scalar().isoformat().startswith('2005')

    with freeze_time("2006-01-01"):
        vote.ballot('counter-proposal')
        session.flush()
        assert vote.last_ballot_change.isoformat().startswith('2006')
        assert session.query(Vote.last_ballot_change
            ).scalar().isoformat().startswith('2006')
        assert vote.last_modified.isoformat().startswith('2006')
        assert session.query(Vote.last_modified
            ).scalar().isoformat().startswith('2006')
    return


def test_vote_meta_data(session: Session) -> None:
    vote = Vote(
        title="Is this a test?",
        shortcode="FOO",
        domain='federation',
        date=date(2015, 6, 14)
    )
    assert not vote.meta

    session.add(vote)
    session.flush()

    assert not vote.meta

    vote.meta['a'] = 1
    assert vote.meta['a'] == 1

    session.flush()
    vote.meta['b'] = 2
    assert vote.meta['a'] == 1
    assert vote.meta['b'] == 2


def test_vote_status(session: Session) -> None:
    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2015, 6, 14)
    )
    assert vote.status is None
    assert vote.completed is False

    session.add(vote)
    session.flush()

    # Set status
    vote.status = 'unknown'
    session.flush()
    assert vote.status == 'unknown'

    vote.status = 'interim'
    session.flush()
    assert vote.status == 'interim'

    vote.status = 'final'
    session.flush()
    assert vote.status == 'final'

    vote.status = None
    session.flush()
    assert vote.status is None

    # Test completed calcuation
    # ... empty vote
    status: Status | None
    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    # ... vote with some results
    vote.proposal.results.append(
        BallotResult(
            name='A',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='B',
            counted=False,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    # ... vote with all results
    session.query(BallotResult).filter_by(name='B').one().counted = True
    for status, completed in (
        (None, True), ('unknown', True), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed


def test_clear_ballot(session: Session) -> None:
    vote = Vote(
        title='Vote',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim'
    )
    vote.proposal.results.append(
        BallotResult(
            entity_id=1,
            name='name',
            counted=True,
            yeas=1,
            nays=2,
            empty=3,
            invalid=4,
        )
    )
    session.add(vote)
    session.flush()
    assert session.query(BallotResult).one()

    vote.proposal.clear_results()
    session.flush()

    assert not vote.proposal.results
    assert session.query(BallotResult).first() is None


def test_clear_vote(session: Session) -> None:
    vote = Vote(
        title='Vote',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim'
    )
    vote.proposal.results.append(
        BallotResult(
            entity_id=1,
            name='name',
            counted=True,
            yeas=1,
            nays=2,
            empty=3,
            invalid=4,
        )
    )
    vote.last_result_change = vote.timestamp()
    session.add(vote)
    session.flush()
    assert session.query(BallotResult).one()

    vote.clear_results()
    session.flush()

    # undo mypy narrowing
    vote = vote
    assert vote.last_result_change is None
    assert vote.status is None
    assert not vote.proposal.results
    assert session.query(BallotResult).first() is None


def test_vote_has_results(session: Session) -> None:
    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2015, 6, 14)
    )
    assert vote.has_results is False

    vote.proposal.results.append(
        BallotResult(
            name='A',
            counted=False,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    assert vote.has_results is False

    vote.proposal.results.append(
        BallotResult(
            name='B',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=2,
        )
    )
    assert vote.has_results is True


def test_vote_rename(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO
) -> None:

    session = election_day_app_zg.session()

    vote = Vote(
        title='Vote',
        id='vorte',
        domain='canton',
        date=date(2017, 1, 1)
    )
    vote.explanations_pdf = (explanations_pdf, 'explanations.pdf')
    assert vote.proposal
    session.add(vote)
    session.flush()

    assert session.query(Ballot.vote_id).one()[0] == 'vorte'

    vote.id = 'vote'
    assert session.query(Ballot.vote_id).one()[0] == 'vote'
    assert len(vote.ballots) == 1

    session.flush()
    assert session.query(Ballot.vote_id).one()[0] == 'vote'
    assert len(vote.ballots) == 1


def test_vote_attachments(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO
) -> None:

    models = tuple(
        cls(
            title="Universal Healthcare",
            domain='federation',
            date=date(2015, 6, 14)
        ) for cls in (Vote, ComplexVote)
    )

    for model in models:
        assert model.explanations_pdf is None
        del model.explanations_pdf
        model.explanations_pdf = (explanations_pdf, 'explanations.pdf')
        # undo mypy narrowing
        model = model
        assert model.explanations_pdf is not None
        assert model.explanations_pdf.name == 'explanations_pdf'
        assert model.explanations_pdf.reference.filename == 'explanations.pdf'
        assert model.explanations_pdf.reference.content_type == (
            'application/pdf')
        del model.explanations_pdf
        assert model.explanations_pdf is None
