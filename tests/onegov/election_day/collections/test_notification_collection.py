from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_notification_collection_trigger(session: Session) -> None:
    collection = NotificationCollection(session)
    all_ = ('email', 'sms', 'webhooks', 'nonexistent')

    election = None
    vote = None
    with freeze_time("2008-01-01"):
        # Add an election, election compound and a vote
        session.add(
            Election(
                title="Election",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        session.add(
            ElectionCompound(
                title="Election",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election_compound = session.query(ElectionCompound).one()

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        assert collection.by_model(election) == []
        assert collection.by_model(election_compound) == []
        assert collection.by_model(vote) == []
        assert collection.by_model(election, current=False) == []
        assert collection.by_model(election_compound, current=False) == []
        assert collection.by_model(vote, current=False) == []

        # No notifications configured
        request: Any = DummyRequest()
        collection.trigger(request, election, all_)
        collection.trigger(request, election_compound, all_)
        collection.trigger(request, vote, all_)

        assert collection.by_model(election) == []
        assert collection.by_model(election_compound) == []
        assert collection.by_model(vote) == []
        assert collection.by_model(election, current=False) == []
        assert collection.by_model(election_compound, current=False) == []
        assert collection.by_model(vote, current=False) == []

        # Add a webhook
        request.app.principal.webhooks = {'https://example.org/1': None}
        collection.trigger(request, election, all_)
        collection.trigger(request, election_compound, all_)
        collection.trigger(request, vote, all_)

        notifications = collection.by_model(election)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].election_id == election.id
        assert notifications[0].last_modified is not None
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        notifications = collection.by_model(election_compound)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].election_compound_id == election_compound.id
        assert notifications[0].last_modified is not None
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        notifications = collection.by_model(vote)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].vote_id == vote.id
        assert notifications[0].last_modified is not None
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        # 'webhooks' not selected
        collection.trigger(request, election, ('email', 'sms'))
        collection.trigger(request, election_compound, ('email', 'sms'))
        collection.trigger(request, vote, ('email', 'sms'))
        notifications = collection.by_model(election)
        assert len(collection.by_model(election)) == 1
        assert len(collection.by_model(election_compound)) == 1
        assert len(collection.by_model(vote)) == 1

    with freeze_time("2009-01-01"):
        # Change the titles
        vote.title = "A vote"
        election.title = "An election"
        election_compound.title = "Some elections"
        session.flush()

        assert collection.by_model(election) == []
        assert collection.by_model(election_compound) == []
        assert collection.by_model(vote) == []

        # Add a email, SMS notification and webhook
        all_ = ('email', 'sms', 'webhooks', 'nonexistent')
        request = DummyRequest(session=session)
        request.app.mail = {'marketing': {'sender': 'info@onegov.ch'}}
        request.app.locales = ['de_CH', 'it_CH', 'fr_CH', 'rm_CH']
        request.app.principal.email_notification = True
        request.app.principal.sms_notification = 'http://example.com'
        request.app.principal.webhooks = {'https://example.org/1': None}
        collection.trigger(request, election, all_)
        collection.trigger(request, election_compound, all_)
        collection.trigger(request, vote, all_)

        notifications = collection.by_model(election)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks'
        ]
        assert all(n.election_id == election.id for n in notifications)
        assert all(n.last_modified.year == 2009 for n in notifications)  # type: ignore[union-attr]

        notifications = collection.by_model(election_compound)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks'
        ]
        assert all(
            n.election_compound_id == election_compound.id
            for n in notifications
        )
        assert all(n.last_modified.year == 2009 for n in notifications)  # type: ignore[union-attr]

        notifications = collection.by_model(vote)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks'
        ]
        assert all(n.vote_id == vote.id for n in notifications)
        assert all(n.last_modified.year == 2009 for n in notifications)  # type: ignore[union-attr]

        # email not selected
        collection.trigger(request, election, ('sms', 'webhooks'))
        collection.trigger(request, election_compound, ('sms', 'webhooks'))
        collection.trigger(request, vote, ('sms', 'webhooks'))

        notifications = collection.by_model(election)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]

        notifications = collection.by_model(election_compound)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]

        notifications = collection.by_model(vote)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]

    assert len(collection.by_model(election, current=False)) == 6
    assert len(collection.by_model(election_compound, current=False)) == 6
    assert len(collection.by_model(vote, current=False)) == 6


def test_notification_collection_trigger_summarized(session: Session) -> None:
    collection = NotificationCollection(session)
    all_ = ('email', 'sms', 'webhooks', 'nonexistent')

    election = None
    vote = None
    with freeze_time("2008-01-01"):
        # Add an election, election compound and a vote
        session.add(
            Election(
                title="Election",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        session.add(
            ElectionCompound(
                title="Elections",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election_compound = session.query(ElectionCompound).one()

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        assert collection.by_model(election) == []
        assert collection.by_model(election_compound) == []
        assert collection.by_model(vote) == []

        # No notifications configured
        request: Any = DummyRequest()
        collection.trigger_summarized(request, [], [], [], all_)
        collection.trigger_summarized(
            request, [election], [election_compound], [vote], all_
        )

        assert collection.by_model(election) == []
        assert collection.by_model(election_compound) == []
        assert collection.by_model(vote) == []

        # Add a webhook
        request.app.principal.webhooks = {'https://example.org/1': None}
        collection.trigger_summarized(
            request, [election], [election_compound], [vote], all_
        )

        notifications = collection.by_model(election)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].election_id == election.id
        assert notifications[0].last_modified is not None
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        notifications = collection.by_model(election_compound)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].election_compound_id == election_compound.id
        assert notifications[0].last_modified is not None
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        notifications = collection.by_model(vote)
        assert len(notifications) == 1
        assert notifications[0].type == 'webhooks'
        assert notifications[0].vote_id == vote.id
        assert notifications[0].last_modified is not None
        assert notifications[0].last_modified.isoformat().startswith('2008-01')

        # 'webhooks' not selected
        collection.trigger_summarized(
            request, [election], [election_compound], [vote], ('email', 'sms')
        )
        assert len(collection.by_model(election)) == 1
        assert len(collection.by_model(election_compound)) == 1
        assert len(collection.by_model(vote)) == 1

    with freeze_time("2009-01-01"):
        # Change the titles
        vote.title = "A vote"
        election.title = "An election"
        election_compound.title = "Some elections"
        session.flush()

        assert collection.by_model(election) == []
        assert collection.by_model(election_compound) == []
        assert collection.by_model(vote) == []

        # Add a email, SMS notification and webhook
        all_ = ('email', 'sms', 'webhooks', 'nonexistent')
        request = DummyRequest(session=session)
        request.app.mail = {'marketing': {'sender': 'info@onegov.ch'}}
        request.app.locales = ['de_CH', 'it_CH', 'fr_CH', 'rm_CH']
        request.app.principal.email_notification = True
        request.app.principal.sms_notification = 'http://example.com'
        request.app.principal.webhooks = {'https://example.org/1': None}
        collection.trigger_summarized(
            request, [election], [election_compound], [vote], all_
        )

        notifications = collection.by_model(election)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks'
        ]
        assert all(n.election_id == election.id for n in notifications)
        assert all(n.last_modified.year == 2009 for n in notifications)  # type: ignore[union-attr]

        notifications = collection.by_model(election_compound)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks'
        ]
        assert all(
            n.election_compound_id == election_compound.id
            for n in notifications
        )
        assert all(n.last_modified.year == 2009 for n in notifications)  # type: ignore[union-attr]

        notifications = collection.by_model(vote)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks'
        ]
        assert all(n.vote_id == vote.id for n in notifications)
        assert all(n.last_modified.year == 2009 for n in notifications)  # type: ignore[union-attr]

        # email not selected
        collection.trigger_summarized(
            request, [election], [election_compound], [vote],
            ('sms', 'webhooks')
        )

        notifications = collection.by_model(election)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]

        notifications = collection.by_model(election_compound)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]

        notifications = collection.by_model(vote)
        assert [n.type for n in notifications] == [
            'email', 'sms', 'webhooks', 'sms', 'webhooks'
        ]
