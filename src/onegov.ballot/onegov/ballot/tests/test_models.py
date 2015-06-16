from datetime import date
from onegov.ballot import Ballot, BallotResult, Contest, Vote


def test_create_all_models(session):
    contest = Contest(date=date(2015, 6, 14))

    session.add(contest)
    session.flush()

    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        contest_date=contest.date,
        elegible_voters=10000,
    )

    session.add(vote)
    session.flush()

    ballot = Ballot(
        question="Do you want pass the universal healthcare act?",
        type='standard',
        vote_id=vote.id
    )

    session.add(ballot)
    session.flush()

    ballot_result = BallotResult(
        group='ZG/Rotkreuz',
        is_established=True,
        yays=4982,
        nays=4452,
        empty=500,
        invalid=66,
        result="Yes",
        ballot_id=ballot.id
    )

    session.add(ballot_result)
    session.flush()


def test_vote_id_generation(session):
    contest = Contest(date=date(2015, 6, 14))

    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        contest_date=contest.date,
        elegible_voters=10000,
    )

    session.add(contest)
    session.add(vote)
    session.flush()

    assert vote.id == 'universal-healthcare'
