from datetime import date
from onegov.ballot import (
    Ballot, BallotCollection, Election, ElectionCollection, Vote,
    VoteCollection
)


def test_elections_by_date(session):
    session.add(Election(
        title="first",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="last",
        domain='canton',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="second",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="ignore",
        domain='canton',
        type='majorz',
        date=date(2015, 6, 12)
    ))

    session.flush()

    collection = ElectionCollection(session)

    # sort by domain, then by date
    assert [v.title for v in collection.by_date(date(2015, 6, 14))] == [
        'first',
        'second',
        'last'
    ]


def test_elections_by_id(session):
    session.add(Election(
        title="first",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="second",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))

    session.flush()

    collection = ElectionCollection(session)

    assert collection.by_id('first').title == "first"
    assert collection.by_id('second').title == "second"


def test_elections_get_latest(session):
    session.add(Election(
        title="latest",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="older",
        domain='canton',
        type='majorz',
        date=date(2015, 6, 12)
    ))

    session.flush()

    collection = ElectionCollection(session)

    # sort by domain, then by date
    assert [v.title for v in collection.get_latest()] == ['latest']


def test_elections_get_years(session):
    session.add(Election(
        title="latest",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="older",
        domain='federation',
        type='majorz',
        date=date(2015, 3, 14)
    ))
    session.add(Election(
        title="even-older",
        domain='canton',
        type='majorz',
        date=date(2013, 6, 12)
    ))

    session.flush()

    assert ElectionCollection(session).get_years() == [2015, 2013]


def test_elections_by_years(session):
    session.add(Election(
        title="latest",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="older",
        domain='canton',
        type='majorz',
        date=date(2014, 6, 12)
    ))

    session.flush()

    elections = ElectionCollection(session, year=2015)
    assert len(elections.by_year()) == 1
    assert elections.by_year()[0].title == "latest"

    assert len(elections.by_year(2014)) == 1
    assert elections.by_year(2014)[0].title == "older"

    assert len(elections.by_year(2013)) == 0


def test_elections_for_years(session):
    elections = ElectionCollection(session, year=2015)
    assert elections.for_year(2016).year == 2016


def test_elections_shortcode_order(session):
    session.add(Election(
        title="A",
        shortcode="Z",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))
    session.add(Election(
        title="Z",
        shortcode="A",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14)
    ))

    session.flush()

    elections = ElectionCollection(session, year=2015).by_year()
    assert elections[0].title == "Z"
    assert elections[1].title == "A"


def test_election_collection_pagination(session):
    elections = ElectionCollection(session)

    assert elections.page_index == 0
    assert elections.pages_count == 0
    assert elections.batch == []

    for year in range(2008, 2011):
        for month in range(1, 13):
            session.add(Election(
                title="Election",
                domain='federation',
                type='majorz',
                date=date(year, month, 1)
            ))
            session.flush()

    assert elections.query().count() == 3 * 12

    elections = ElectionCollection(session)
    assert elections.subset_count == 3 * 12

    elections = ElectionCollection(session, year='2007')
    assert elections.subset_count == 0

    elections = ElectionCollection(session, year='2008')
    assert elections.subset_count == 12
    assert all([e.date.year == 2008 for e in elections.batch])
    assert all([e.date.month > 2 for e in elections.batch])
    assert len(elections.next.batch) == 12 - elections.batch_size
    assert all([e.date.year == 2008 for e in elections.next.batch])
    assert all([e.date.month < 3 for e in elections.next.batch])

    elections = ElectionCollection(session, year='2009')
    assert elections.subset_count == 12
    assert all([e.date.year == 2009 for e in elections.batch])
    assert all([e.date.month > 2 for e in elections.batch])
    assert len(elections.next.batch) == 12 - elections.batch_size
    assert all([e.date.year == 2009 for e in elections.next.batch])
    assert all([e.date.month < 3 for e in elections.next.batch])

    elections = ElectionCollection(session, year='2010')
    assert elections.subset_count == 12
    assert all([e.date.year == 2010 for e in elections.batch])
    assert all([e.date.month > 2 for e in elections.batch])
    assert len(elections.next.batch) == 12 - elections.batch_size
    assert all([e.date.year == 2010 for e in elections.next.batch])
    assert all([e.date.month < 3 for e in elections.next.batch])


def test_votes_by_date(session):
    session.add(Vote(
        title="first",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="last",
        domain='canton',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="second",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="ignore",
        domain='canton',
        date=date(2015, 6, 12)
    ))

    session.flush()

    collection = VoteCollection(session)

    # sort by domain, then by date
    assert [v.title for v in collection.by_date(date(2015, 6, 14))] == [
        'first',
        'second',
        'last'
    ]


def test_votes_by_id(session):
    session.add(Vote(
        title="first",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="second",
        domain='federation',
        date=date(2015, 6, 14)
    ))

    session.flush()

    collection = VoteCollection(session)

    assert collection.by_id('first').title == "first"
    assert collection.by_id('second').title == "second"


def test_votes_get_latest(session):
    session.add(Vote(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="older",
        domain='canton',
        date=date(2015, 6, 12)
    ))

    session.flush()

    collection = VoteCollection(session)

    # sort by domain, then by date
    assert [v.title for v in collection.get_latest()] == ['latest']


def test_votes_get_years(session):
    session.add(Vote(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="older",
        domain='federation',
        date=date(2015, 3, 14)
    ))
    session.add(Vote(
        title="even-older",
        domain='canton',
        date=date(2013, 6, 12)
    ))

    session.flush()

    assert VoteCollection(session).get_years() == [2015, 2013]


def test_votes_by_years(session):
    session.add(Vote(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="older",
        domain='canton',
        date=date(2014, 6, 12)
    ))

    session.flush()

    votes = VoteCollection(session, year=2015)
    assert len(votes.by_year()) == 1
    assert votes.by_year()[0].title == "latest"

    assert len(votes.by_year(2014)) == 1
    assert votes.by_year(2014)[0].title == "older"

    assert len(votes.by_year(2013)) == 0


def test_votes_for_years(session):
    votes = VoteCollection(session, year=2015)
    assert votes.for_year(2016).year == 2016


def test_votes_shortcode_order(session):
    session.add(Vote(
        title="A",
        shortcode="Z",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="Z",
        shortcode="A",
        domain='federation',
        date=date(2015, 6, 14)
    ))

    session.flush()

    votes = VoteCollection(session, year=2015).by_year()
    assert votes[0].title == "Z"
    assert votes[1].title == "A"


def test_ballot_collection(session):
    vote = Vote(
        title="A",
        shortcode="Z",
        domain='federation',
        date=date(2015, 6, 14)
    )
    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    collection = BallotCollection(session)

    assert collection.query().count() == 1
    assert collection.by_id(vote.ballots[0].id) == vote.ballots[0]


def test_vote_collection_pagination(session):
    votes = VoteCollection(session)

    assert votes.page_index == 0
    assert votes.pages_count == 0
    assert votes.batch == []

    for year in range(2008, 2011):
        for month in range(1, 13):
            session.add(Vote(
                title="Vote",
                domain='federation',
                date=date(year, month, 1)
            ))
            session.flush()

    assert votes.query().count() == 3 * 12

    votes = VoteCollection(session)
    assert votes.subset_count == 3 * 12

    votes = VoteCollection(session, year='2007')
    assert votes.subset_count == 0

    votes = VoteCollection(session, year='2008')
    assert votes.subset_count == 12
    assert all([e.date.year == 2008 for e in votes.batch])
    assert all([e.date.month > 2 for e in votes.batch])
    assert len(votes.next.batch) == 12 - votes.batch_size
    assert all([e.date.year == 2008 for e in votes.next.batch])
    assert all([e.date.month < 3 for e in votes.next.batch])

    votes = VoteCollection(session, year='2009')
    assert votes.subset_count == 12
    assert all([e.date.year == 2009 for e in votes.batch])
    assert all([e.date.month > 2 for e in votes.batch])
    assert len(votes.next.batch) == 12 - votes.batch_size
    assert all([e.date.year == 2009 for e in votes.next.batch])
    assert all([e.date.month < 3 for e in votes.next.batch])

    votes = VoteCollection(session, year='2010')
    assert votes.subset_count == 12
    assert all([e.date.year == 2010 for e in votes.batch])
    assert all([e.date.month > 2 for e in votes.batch])
    assert len(votes.next.batch) == 12 - votes.batch_size
    assert all([e.date.year == 2010 for e in votes.next.batch])
    assert all([e.date.month < 3 for e in votes.next.batch])
