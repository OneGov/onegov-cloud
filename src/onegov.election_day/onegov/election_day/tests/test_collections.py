from datetime import date, datetime, timezone
from freezegun import freeze_time
from onegov.ballot.models import Election, Vote
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.tests import DummyRequest
from uuid import uuid4


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


def test_archive_grouping(session):
    for domain in ('federation', 'canton', 'municipality'):
        session.add(
            Election(
                title="{} election 1".format(domain),
                domain=domain,
                type='majorz',
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
                type='majorz',
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

    ids_i = sorted([r.meta['id'] for r in archive.query()])
    ids_a = [r.id for r in elections.values()] + [r.id for r in votes.values()]
    assert ids_i == ['election-2001', 'vote-2001']
    assert set(ids_i).issubset(set(ids_a))

    archive.update_all(request)

    assert archive.get_years() == [2002, 2001]
    assert archive.query().count() == 4

    ids_i = sorted([r.meta['id'] for r in archive.query()])
    ids_a = [r.id for r in elections.values()] + [r.id for r in votes.values()]
    assert ids_i == [
        'election-2001', 'election-2002', 'vote-2001', 'vote-2002'
    ]
    assert set(ids_i).issubset(set(ids_a))

    archive.add(elections[2003], request)
    archive.add(votes[2003], request)

    assert archive.get_years() == [2003, 2002, 2001]
    assert archive.query().count() == 6

    ids_i = sorted([r.meta['id'] for r in archive.query()])
    ids_a = [r.id for r in elections.values()] + [r.id for r in votes.values()]
    assert set(ids_i) == set(ids_a)

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
    assert result.meta['id'] == 'election-2001'
    assert result.meta['elected_candidates'] == []

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
    assert result.meta['id'] == 'vote-2001'


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
    subscriber = collection.query().one()
    assert subscriber.phone_number == '+41791112233'
    assert subscriber.locale == 'de_CH'
    assert collection.by_id(subscriber.id) == subscriber

    collection.subscribe('+41791112233', 'de_CH')
    subscriber = collection.query().one()
    assert subscriber.phone_number == '+41791112233'
    assert subscriber.locale == 'de_CH'

    collection.subscribe('+41791112233', 'en')
    subscriber = collection.query().one()
    assert subscriber.phone_number == '+41791112233'
    assert subscriber.locale == 'en'

    collection.subscribe('+41792223344', 'de_CH')
    assert collection.query().count() == 2

    collection.unsubscribe('+41791112233')
    assert collection.query().one().phone_number == '+41792223344'

    collection.unsubscribe('+41791112233')
    assert collection.query().count() == 1

    collection.unsubscribe('+41792223344')
    assert collection.query().count() == 0


def test_subscriber_collection_pagination(session):

    collection = SubscriberCollection(session)
    for number in range(100):
        collection.subscribe('+417911122{:02}'.format(number), 'de_CH')
    assert collection.query().count() == 100

    assert SubscriberCollection(session, page=0).batch[0].phone_number == \
        '+41791112200'
    assert SubscriberCollection(session, page=4).batch[4].phone_number == \
        '+41791112244'
    assert SubscriberCollection(session, page=5).batch[5].phone_number == \
        '+41791112255'
    assert SubscriberCollection(session, page=9).batch[9].phone_number == \
        '+41791112299'

    assert len(SubscriberCollection(session, page=10).batch) == 0


def test_subscriber_collection_term(session):

    collection = SubscriberCollection(session)
    for number in range(100):
        collection.subscribe('+417911122{:02}'.format(number), 'de_CH')
    assert collection.query().count() == 100

    collection = SubscriberCollection(session, term='+417911122')
    assert collection.query().count() == 100

    collection = SubscriberCollection(session, term='+41791112200')
    assert collection.query().one().phone_number == '+41791112200'

    collection = SubscriberCollection(session, term='2200')
    assert collection.query().one().phone_number == '+41791112200'

    collection = SubscriberCollection(session, term='220')
    assert collection.query().count() == 11


def test_data_source_collection(session):
    collection = DataSourceCollection(session)

    collection.add(DataSource(type='vote', name='ds_vote'))
    data_source = collection.query().one()
    assert data_source.type == 'vote'
    assert data_source.name == 'ds_vote'
    assert collection.by_id(data_source.id) == data_source

    collection.delete(data_source)
    assert collection.query().count() == 0


def test_data_source_collection_pagination(session):
    collection = DataSourceCollection(session)

    for number in range(100):
        collection.add(DataSource(type='vote', name='{:02}'.format(number)))
    assert collection.query().count() == 100

    assert DataSourceCollection(session, page=0).batch[0].name == '00'
    assert DataSourceCollection(session, page=4).batch[4].name == '44'
    assert DataSourceCollection(session, page=5).batch[5].name == '55'
    assert DataSourceCollection(session, page=9).batch[9].name == '99'

    assert len(DataSourceCollection(session, page=10).batch) == 0


def test_data_source_item_collection(session):
    DataSourceCollection(session).add(DataSource(type='vote', name='ds'))
    data_source = session.query(DataSource).one()

    collection = DataSourceItemCollection(session, id=data_source.id)
    assert collection.source is data_source

    collection.add(DataSourceItem(number='1', district='2'))
    item = collection.query().one()
    assert item.number == '1'
    assert item.district == '2'
    assert collection.by_id(item.id) == item

    collection.delete(item)
    assert collection.query().count() == 0


def test_data_source_item_collection_pagination(session):
    id_ = uuid4()
    DataSourceCollection(session).add(
        DataSource(type='vote', name='ds', id=id_)
    )
    collection = DataSourceItemCollection(session, id=id_)

    for number in range(100):
        collection.add(DataSourceItem(number='{:02}'.format(number)))
    assert collection.query().count() == 100

    assert DataSourceItemCollection(session, id=id_, page=0).batch[0].number \
        == '00'
    assert DataSourceItemCollection(session, id=id_, page=4).batch[4].number \
        == '44'
    assert DataSourceItemCollection(session, id=id_, page=5).batch[5].number \
        == '55'
    assert DataSourceItemCollection(session, id=id_, page=9).batch[9].number \
        == '99'

    assert len(DataSourceItemCollection(session, page=10).batch) == 0


def test_upload_token_collection(session):

    collection = UploadTokenCollection(session)
    assert collection.list() == []

    token = collection.create()
    assert collection.list() == [token]

    token = collection.create(token=token)
    assert collection.list() == [token]

    another_token = collection.create(token=uuid4())
    assert set(collection.list()) == set([token, another_token])

    collection.delete(token)
    assert collection.list() == [another_token]

    collection.create()
    collection.create()
    collection.create()
    assert len(collection.list()) == 4

    collection.clear()
    assert collection.list() == []
