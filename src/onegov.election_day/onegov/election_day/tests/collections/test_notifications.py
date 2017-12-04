from datetime import date
from freezegun import freeze_time
from onegov.ballot.models import Election
from onegov.ballot.models import Vote
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.tests import DummyRequest


def test_notification_collection(session):
    collection = NotificationCollection(session)

    election = None
    vote = None
    with freeze_time("2008-01-01"):
        # Add an election and a vote
        session.add(
            Election(
                title="Election",
                domain='federation',
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

        # No notifications configured
        request = DummyRequest()
        collection.trigger(request, election)
        collection.trigger(request, vote)

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        # Add a webhook
        request.app.principal.webhooks = {'http://abc.com/1': None}
        collection.trigger(request, election)
        collection.trigger(request, vote)

        notifications = collection.by_election(election)
        assert len(notifications) == 1
        assert notifications[0].action == 'webhooks'
        assert notifications[0].election_id == election.id
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        notifications = collection.by_vote(vote)
        assert len(notifications) == 1
        assert notifications[0].action == 'webhooks'
        assert notifications[0].vote_id == vote.id
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

    with freeze_time("2009-01-01"):
        vote.title = "A vote"
        election.title = "An election"
        session.flush()

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        # Add a webhook and SMS notification
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
        assert notifications[0].last_modified.isoformat().startswith('2009-01')
        assert notifications[1].last_modified.isoformat().startswith('2009-01')

        notifications = collection.by_vote(vote)
        assert len(notifications) == 2
        assert notifications[0].action in ('webhooks', 'sms')
        assert notifications[1].action in ('webhooks', 'sms')
        assert notifications[0].action != notifications[1].action
        assert notifications[0].vote_id == vote.id
        assert notifications[1].vote_id == vote.id
        assert notifications[0].last_modified.isoformat().startswith('2009-01')
        assert notifications[1].last_modified.isoformat().startswith('2009-01')

        collection.trigger(request, election)
        collection.trigger(request, vote)
        assert len(collection.by_election(election)) == 4
        assert len(collection.by_vote(vote)) == 4
