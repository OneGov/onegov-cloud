from datetime import date
from freezegun import freeze_time
from onegov.ballot.models import Election
from onegov.ballot.models import Vote
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.tests import DummyRequest


def test_notification_collection(session):
    collection = NotificationCollection(session)
    all_ = ('email', 'sms', 'webhooks')

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
        collection.trigger(request, election, all_)
        collection.trigger(request, vote, all_)

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        # Add a webhook
        request.app.principal.webhooks = {'http://abc.com/1': None}
        collection.trigger(request, election, all_)
        collection.trigger(request, vote, all_)

        notifications = collection.by_election(election)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].election_id == election.id
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        notifications = collection.by_vote(vote)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].vote_id == vote.id
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        # 'webhooks' not selected
        collection.trigger(request, election, ('email', 'sms'))
        collection.trigger(request, vote, ('email', 'sms'))
        notifications = collection.by_election(election)
        assert len(collection.by_election(election)) == 1
        assert len(collection.by_vote(vote)) == 1

    with freeze_time("2009-01-01"):
        # Change the election and vote titles
        vote.title = "A vote"
        election.title = "An election"
        session.flush()

        assert collection.by_election(election) == []
        assert collection.by_vote(vote) == []

        # Add a email, SMS notification and webhook
        request = DummyRequest(session=session)
        request.app.mail = {'marketing': {'sender': 'info@onegov.ch'}}
        request.app.locales = ['de_CH', 'it_CH', 'fr_CH', 'rm_CH']
        request.app.principal.email_notification = True
        request.app.principal.sms_notification = 'http://example.com'
        request.app.principal.webhooks = {'http://abc.com/1': None}
        collection.trigger(request, election, all_)
        collection.trigger(request, vote, all_)

        notifications = collection.by_election(election)
        assert len(notifications) == 3
        assert [n.type for n in notifications] == ['email', 'sms', 'webhooks']
        assert all(n.election_id == election.id for n in notifications)
        assert all(n.last_modified.year == 2009 for n in notifications)

        notifications = collection.by_vote(vote)
        assert len(notifications) == 3
        assert [n.type for n in notifications] == ['email', 'sms', 'webhooks']
        assert all(n.vote_id == vote.id for n in notifications)
        assert all(n.last_modified.year == 2009 for n in notifications)

        # 'email' not selected
        collection.trigger(request, election, ('sms', 'webhooks'))
        collection.trigger(request, vote, ('sms', 'webhooks'))

        notifications = collection.by_election(election)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]

        notifications = collection.by_vote(vote)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]

        # 'sms' not selected
        collection.trigger(request, election, ('email', 'webhooks'))
        collection.trigger(request, vote, ('email', 'webhooks'))

        notifications = collection.by_election(election)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks', 'email', 'webhooks'
        ]

        notifications = collection.by_vote(vote)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks', 'email', 'webhooks'
        ]
