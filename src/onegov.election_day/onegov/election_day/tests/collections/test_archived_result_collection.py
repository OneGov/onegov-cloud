from datetime import date
from onegov.ballot.models import Ballot
from onegov.ballot.models import BallotResult
from onegov.ballot.models import Election
from onegov.ballot.models import ElectionResult
from onegov.ballot.models import Vote
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.tests import DummyRequest


def test_archived_result_collection(session):
    archive = ArchivedResultCollection(session)

    assert archive.for_date(2015).date == 2015
    assert archive.for_date('2015').date == '2015'
    assert archive.for_date('2015-01-01').date == '2015-01-01'

    assert archive.get_years() == []
    assert archive.latest() == ([], None)
    assert archive.for_date(2015).by_date() == ([], None)
    assert archive.for_date('2015').by_date() == ([], None)
    assert archive.for_date('2015-01-01').by_date() == ([], None)
    assert archive.for_date(2015).by_year(2015) == ([], None)
    assert archive.for_date('2015').by_year('2015') == ([], None)

    for year in (2009, 2011, 2014, 2016):
        session.add(
            Election(
                title="Election {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )
    for year in (2007, 2011, 2015, 2016):
        session.add(
            Vote(
                title="Vote {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )

    session.flush()

    archive.update_all(DummyRequest())

    assert archive.get_years() == [2016, 2015, 2014, 2011, 2009, 2007]

    for date_ in (2016, '2016', '2016-01-01'):
        assert archive.latest() == archive.for_date(date_).by_date()

    assert archive.for_date('2016-02-02').by_date() == ([], None)

    for year in (2009, 2011, 2014, 2016):
        item = session.query(ArchivedResult)
        item = item.filter_by(date=date(year, 1, 1), type='election').one()
        items, modified = archive.for_date(year).by_date()
        assert item in items
        items, modified = archive.for_date(str(year)).by_date()
        assert item in items
        items, modified = archive.by_year(year)
        assert item in items
        items, modified = archive.by_year(str(year))
        assert item in items

        groups = archive.group_items(items, DummyRequest())
        assert groups[date(year, 1, 1)]['federation']['election'] == [item]

    for year in (2007, 2011, 2015, 2016):
        item = session.query(ArchivedResult)
        item = item.filter_by(date=date(year, 1, 1), type='vote').one()
        items, modified = archive.for_date(year).by_date()
        assert item in items
        items, modified = archive.for_date(str(year)).by_date()
        assert item in items
        items, modified = archive.by_year(year)
        assert item in items
        items, modified = archive.by_year(str(year))
        assert item in items

        groups = archive.group_items(items, DummyRequest())
        assert groups[date(year, 1, 1)]['federation']['vote'] == [item]


def test_archived_result_collection_grouping(session):
    for domain in ('federation', 'canton', 'municipality'):
        session.add(
            Election(
                title="{} election 1".format(domain),
                domain=domain,
                date=date(2017, 2, 12)
            )
        )
        session.add(
            Vote(
                title="{} vote 1".format(domain),
                domain=domain,
                date=date(2017, 2, 12)
            )
        )

        session.add(
            Election(
                title="{} election 2".format(domain),
                domain=domain,
                date=date(2017, 5, 21)
            )
        )
        session.add(
            Vote(
                title="{} vote 2".format(domain),
                domain=domain,
                date=date(2017, 5, 21)
            )
        )

    session.flush()

    archive = ArchivedResultCollection(session).for_date(2017)

    request = DummyRequest()
    archive.update_all(request)

    items, last_modified = archive.by_date()

    request.app.principal.domain = 'federation'
    expected = ['federation', 'canton', 'municipality']

    grouped = archive.group_items(items, request)
    assert list(grouped) == [date(2017, 2, 12), date(2017, 5, 21)]
    assert all([list(group) == expected for group in grouped.values()])

    request.app.principal.domain = 'canton'

    grouped = archive.group_items(items, request)
    grouped = archive.group_items(items, request)
    assert list(grouped) == [date(2017, 2, 12), date(2017, 5, 21)]
    assert all([list(group) == expected for group in grouped.values()])

    request.app.principal.domain = 'municipality'
    expected = ['municipality', 'federation', 'canton']

    grouped = archive.group_items(items, request)
    assert list(grouped) == [date(2017, 2, 12), date(2017, 5, 21)]
    assert all([list(group) == expected for group in grouped.values()])


def test_archived_result_collection_updates(session):
    archive = ArchivedResultCollection(session)
    request = DummyRequest()

    # Add elections and votes
    elections = {
        year: Election(
            title="Election {}".format(year),
            domain='federation',
            date=date(year, 1, 1),
        ) for year in (2001, 2002, 2003)
    }
    votes = {
        year: Vote(
            title="Vote {}".format(year),
            domain='federation',
            date=date(year, 1, 1),
        ) for year in (2001, 2002, 2003)
    }

    session.add(elections[2001])
    session.add(elections[2002])
    session.add(votes[2001])
    session.add(votes[2002])

    session.flush()

    # Test get_years / query
    assert archive.get_years() == []

    archive.update(elections[2001], request)
    archive.update(votes[2001], request)

    assert archive.get_years() == [2001]
    assert archive.query().count() == 2

    ids_i = sorted([r.external_id for r in archive.query()])
    ids_a = [r.id for r in elections.values()] + [r.id for r in votes.values()]
    assert ids_i == ['election-2001', 'vote-2001']
    assert set(ids_i).issubset(set(ids_a))

    archive.update_all(request)

    assert archive.get_years() == [2002, 2001]
    assert archive.query().count() == 4

    ids_i = sorted([r.external_id for r in archive.query()])
    ids_a = [r.id for r in elections.values()] + [r.id for r in votes.values()]
    assert ids_i == [
        'election-2001', 'election-2002', 'vote-2001', 'vote-2002'
    ]
    assert set(ids_i).issubset(set(ids_a))

    archive.add(elections[2003], request)
    archive.add(votes[2003], request)

    assert archive.get_years() == [2003, 2002, 2001]
    assert archive.query().count() == 6

    ids_i = sorted([r.external_id for r in archive.query()])
    ids_a = [r.id for r in elections.values()] + [r.id for r in votes.values()]
    assert set(ids_i) == set(ids_a)

    archive.delete(elections[2002], request)
    archive.delete(votes[2002], request)

    assert archive.get_years() == [2003, 2001]
    assert archive.query().count() == 4

    # Test update election
    result = archive.update(elections[2001], request)
    assert result.url == 'Election/election-2001'
    assert result.schema
    assert result.domain == 'federation'
    assert result.date == date(2001, 1, 1)
    assert result.shortcode is None
    assert result.title == 'Election 2001'
    assert result.title_translations == {'de_CH': 'Election 2001'}
    assert result.last_modified is not None
    assert result.last_result_change is None
    assert result.type == 'election'
    assert result.counted_entities is None
    assert result.total_entities is None
    assert result.progress == (0, 0)
    assert result.external_id == 'election-2001'
    assert result.elected_candidates == []

    elections[2001].title = 'Election'
    elections[2001].shortcode = 'shortcode'
    result = archive.update(elections[2001], request)

    assert result.last_modified is not None
    assert result.last_result_change is None
    assert result.title == 'Election'
    assert result.shortcode == 'shortcode'
    assert result.title_translations == {'de_CH': 'Election'}

    elections[2001].results.append(
        ElectionResult(
            name='name',
            entity_id=1,
            elegible_voters=100,
            received_ballots=50,
            blank_ballots=2,
            invalid_ballots=5,
            blank_votes=4,
            invalid_votes=3
        )
    )
    result = archive.update(elections[2001], request)
    assert result.last_result_change is not None

    # Test update vote
    result = archive.update(votes[2001], request)
    assert result.url == 'Vote/vote-2001'
    assert result.schema
    assert result.domain == 'federation'
    assert result.date == date(2001, 1, 1)
    assert result.shortcode is None
    assert result.title == 'Vote 2001'
    assert result.title_translations == {'de_CH': 'Vote 2001'}
    assert result.last_modified is not None
    assert result.last_result_change is None

    votes[2001].title = 'Vote'
    votes[2001].shortcode = 'shortcode'
    result = archive.update(votes[2001], request)

    assert result.last_modified is not None
    assert result.last_result_change is None
    assert result.title == 'Vote'
    assert result.shortcode == 'shortcode'
    assert result.title_translations == {'de_CH': 'Vote'}
    assert result.external_id == 'vote-2001'

    votes[2001].ballots.append(Ballot(type='proposal'))
    votes[2001].proposal.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1
        )
    )
    result = archive.update(votes[2001], request)
    assert result.last_result_change is not None
