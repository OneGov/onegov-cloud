from datetime import date, datetime, timezone
from freezegun import freeze_time
from onegov.ballot.models import Election, Vote
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.tests import DummyRequest


def test_archive(session):
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
                type='majorz',
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

        groups = archive.group_items(items)
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

        groups = archive.group_items(items)
        assert groups[date(year, 1, 1)]['federation']['vote'] == [item]


def test_archived_results(session):
    archive = ArchivedResultCollection(session)
    request = DummyRequest()

    elections = {
        year: Election(
            title="Election {}".format(year),
            domain='federation',
            type='majorz',
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

    assert archive.get_years() == []

    archive.update(elections[2001], request)
    archive.update(votes[2001], request)

    assert archive.get_years() == [2001]
    assert archive.query().count() == 2

    archive.update_all(request)

    assert archive.get_years() == [2002, 2001]
    assert archive.query().count() == 4

    archive.add(elections[2003], request)
    archive.add(votes[2003], request)

    assert archive.get_years() == [2003, 2002, 2001]
    assert archive.query().count() == 6

    archive.delete(elections[2002], request)
    archive.delete(votes[2002], request)

    assert archive.get_years() == [2003, 2001]
    assert archive.query().count() == 4

    result = archive.update(elections[2001], request)
    assert result.url == 'Election/election-2001'
    assert result.schema
    assert result.domain == 'federation'
    assert result.date == date(2001, 1, 1)
    assert result.shortcode == None
    assert result.title == 'Election 2001'
    assert result.title_translations == {'de_CH': 'Election 2001'}
    assert result.last_result_change
    assert result.type == 'election'
    assert result.counted_entities == None
    assert result.total_entities == None
    assert result.progress == (0, 0)

    last_result_change = result.last_result_change

    elections[2001].title = 'Election'
    elections[2001].shortcode = 'shortcode'
    result = archive.update(elections[2001], request)

    assert result.last_result_change != last_result_change
    assert result.title == 'Election'
    assert result.shortcode == 'shortcode'
    assert result.title_translations == {'de_CH': 'Election'}

    result = archive.update(votes[2001], request)
    result.url = 'Vote/vote-2001'
    result.schema
    result.domain = 'federation'
    result.date = date(2001, 1, 1)
    result.shortcode = None
    result.title = 'Vote 2001'
    result.title_translations = {'de_CH': 'Vote 2001'}
    result.last_result_change

    last_result_change = result.last_result_change

    votes[2001].title = 'Vote'
    votes[2001].shortcode = 'shortcode'
    result = archive.update(votes[2001], request)

    assert result.last_result_change != last_result_change
    assert result.title == 'Vote'
    assert result.shortcode == 'shortcode'
    assert result.title_translations == {'de_CH': 'Vote'}


def test_notification_collection(session):
    collection = NotificationCollection(session)

    election = None
    vote = None
    with freeze_time("2008-01-01 00:00"):
        session.add(
            Election(
                title="Election",
                domain='federation',
                type='majorz',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        request = DummyRequest()
        collection.trigger(request, election)
        collection.trigger(request, vote)

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        request.app.principal.webhooks = {'http://abc.com/1': None}
        collection.trigger(request, election)
        collection.trigger(request, vote)

        notifications = collection.by_election(election)
        assert len(notifications) == 1
        assert notifications[0].action == 'webhooks'
        assert notifications[0].election_id == election.id
        assert notifications[0].last_change == datetime(2008, 1, 1, 0, 0,
                                                        tzinfo=timezone.utc)

        notifications = collection.by_vote(vote)
        assert len(notifications) == 1
        assert notifications[0].action == 'webhooks'
        assert notifications[0].vote_id == vote.id
        assert notifications[0].last_change == datetime(2008, 1, 1, 0, 0,
                                                        tzinfo=timezone.utc)

    with freeze_time("2009-01-01 00:00"):
        vote.title = "A vote"
        election.title = "An election"
        session.flush()

        freezed = datetime(2009, 1, 1, 0, 0, tzinfo=timezone.utc)

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        request = DummyRequest(session=session)
        request.app.principal.webhooks = {'http://abc.com/1': None}
        request.app.principal.sms_notification = 'http://example.com'
        collection.trigger(request, election)
        collection.trigger(request, vote)

        notifications = collection.by_election(election)
        assert len(notifications) == 2
        assert notifications[0].action in ('webhooks', 'sms')
        assert notifications[1].action in ('webhooks', 'sms')
        assert notifications[0].action != notifications[1].action
        assert notifications[0].election_id == election.id
        assert notifications[1].election_id == election.id
        assert notifications[0].last_change == freezed
        assert notifications[1].last_change == freezed

        notifications = collection.by_vote(vote)
        assert len(notifications) == 2
        assert notifications[0].action in ('webhooks', 'sms')
        assert notifications[1].action in ('webhooks', 'sms')
        assert notifications[0].action != notifications[1].action
        assert notifications[0].vote_id == vote.id
        assert notifications[1].vote_id == vote.id
        assert notifications[0].last_change == freezed
        assert notifications[1].last_change == freezed

        collection.trigger(request, election)
        collection.trigger(request, vote)
        assert len(collection.by_election(election)) == 4
        assert len(collection.by_vote(vote)) == 4


def test_subscriber_collection(session):

    collection = SubscriberCollection(session)
    collection.subscribe('+41791112233', 'de_CH')
    assert collection.query().one().phone_number == '+41791112233'
    assert collection.query().one().locale == 'de_CH'

    collection.subscribe('+41791112233', 'de_CH')
    assert collection.query().one().phone_number == '+41791112233'
    assert collection.query().one().locale == 'de_CH'

    collection.subscribe('+41791112233', 'en')
    assert collection.query().one().phone_number == '+41791112233'
    assert collection.query().one().locale == 'en'

    collection.subscribe('+41792223344', 'de_CH')
    assert collection.query().count() == 2

    collection.unsubscribe('+41791112233')
    assert collection.query().one().phone_number == '+41792223344'

    collection.unsubscribe('+41791112233')
    assert collection.query().count() == 1

    collection.unsubscribe('+41792223344')
    assert collection.query().count() == 0
