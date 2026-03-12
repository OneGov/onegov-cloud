from __future__ import annotations

from datetime import date
from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.forms import TriggerNotificationsForm
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_notification_form() -> None:
    form = TriggerNotificationForm()
    form.request = DummyRequest()  # type: ignore[assignment]
    form.on_request()
    assert form.notifications.choices == []
    assert not form.validate()

    form.request.app.principal.email_notification = True
    form.on_request()
    assert form.notifications.choices == [('email', 'Email')]
    assert 'email' in form.notifications.default  # type: ignore[operator]

    form.request.app.principal.sms_notification = 'http://example.com'
    form.on_request()
    assert form.notifications.choices == [('email', 'Email'), ('sms', 'SMS')]
    assert 'sms' in form.notifications.default  # type: ignore[operator]

    form.request.app.principal.webhooks = {'https://example.org/1': {}}
    form.on_request()
    assert form.notifications.choices == [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhooks', 'Webhooks')
    ]
    assert form.notifications.data == ['email', 'sms', 'webhooks']
    assert 'webhooks' in form.notifications.default  # type: ignore[operator]


def test_notifications_form(session: Session) -> None:
    form = TriggerNotificationsForm()
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.on_request()
    assert form.notifications.choices == []
    assert form.elections.choices == []
    assert form.election_compounds.choices == []
    assert form.votes.choices == []
    assert form.latest_date(session) is None
    assert not form.validate()

    # Enable notification
    form.request.app.principal.email_notification = True
    form.request.app.principal.sms_notification = 'http://example.com'
    form.request.app.principal.webhooks = {'https://example.org/1': {}}

    # Add votes and elections
    session.add(
        Vote(
            title='Vote 1',
            shortcode='f',
            domain='canton',
            date=date(2015, 1, 1)
        )
    )
    session.add(
        Vote(
            title='Vote 2',
            shortcode='e',
            domain='federation',
            date=date(2015, 2, 1)
        )
    )
    session.add(
        Vote(
            title='Vote 3',
            shortcode='d',
            domain='canton',
            date=date(2015, 2, 1)
        )
    )
    session.add(
        Election(
            title='Majorz Election 1',
            shortcode='c',
            domain='canton',
            date=date(2015, 2, 1)
        )
    )
    session.add(
        Election(
            title='Majorz Election 2',
            shortcode='b',
            domain='region',
            date=date(2015, 2, 1)
        )
    )
    session.add(
        ProporzElection(
            title='Proporz Election',
            shortcode='a',
            domain='canton',
            date=date(2015, 1, 10)
        )
    )
    session.add(
        ElectionCompound(
            title='Elections',
            shortcode='a',
            domain='federation',
            date=date(2015, 2, 1)
        )
    )
    session.flush()

    # Test on_request
    form.on_request()
    assert form.notifications.choices == [
        ('email', 'Email'), ('sms', 'SMS'), ('webhooks', 'Webhooks')
    ]
    assert form.notifications.data == [
        'email', 'sms', 'webhooks'
    ]
    assert form.notifications.default is not None
    assert 'email' in form.notifications.default
    assert 'sms' in form.notifications.default
    assert 'webhooks' in form.notifications.default
    assert form.latest_date(session) == date(2015, 2, 1)
    assert form.votes.choices == [
        ('vote-3', 'Vote 3'),
        ('vote-2', 'Vote 2')
    ]
    assert form.elections.choices == [
        ('majorz-election-2', 'Majorz Election 2'),
        ('majorz-election-1', 'Majorz Election 1')
    ]
    assert form.election_compounds.choices == [
        ('elections', 'Elections'),
    ]
    assert form.vote_models(session) == []
    assert form.election_models(session) == []
    assert form.election_compound_models(session) == []

    # Test submit
    form = TriggerNotificationsForm(
        DummyPostData({'notifications': ['email']})
    )
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.app.principal.email_notification = True
    form.on_request()
    assert not form.validate()

    form = TriggerNotificationsForm(
        DummyPostData({
            'notifications': ['email'],
            'votes': ['vote-3', 'vote-2'],
            'elections': ['majorz-election-2'],
            'election_compounds': ['elections']
        })
    )
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.app.principal.email_notification = True
    form.on_request()
    assert form.validate()
    assert [x.id for x in form.vote_models(session)] == [
        'vote-3',
        'vote-2'
    ]
    assert [x.id for x in form.election_models(session)] == [
        'majorz-election-2',
    ]
    assert [x.id for x in form.election_compound_models(session)] == [
        'elections',
    ]
