from datetime import date, datetime, timezone
from freezegun import freeze_time
from onegov.ballot.models import Election, Vote
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.tests import DummyRequest


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

        request.app.principal.webhooks = ['http://abc.com/1']
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

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        request = DummyRequest()
        request.app.principal.webhooks = ['http://abc.com/1']
        collection.trigger(request, election)
        collection.trigger(request, vote)

        notifications = collection.by_election(election)
        assert len(notifications) == 1
        assert notifications[0].action == 'webhooks'
        assert notifications[0].election_id == election.id
        assert notifications[0].last_change == datetime(2009, 1, 1, 0, 0,
                                                        tzinfo=timezone.utc)

        notifications = collection.by_vote(vote)
        assert len(notifications) == 1
        assert notifications[0].action == 'webhooks'
        assert notifications[0].vote_id == vote.id
        assert notifications[0].last_change == datetime(2009, 1, 1, 0, 0,
                                                        tzinfo=timezone.utc)

        collection.trigger(request, election)
        collection.trigger(request, vote)
        assert len(collection.by_election(election)) == 2
        assert len(collection.by_vote(vote)) == 2
