from datetime import date
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.ballot import Vote
from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.forms import TriggerNotificationsForm
from onegov.election_day.tests.common import DummyPostData
from onegov.election_day.tests.common import DummyRequest


def test_notification_form():
    form = TriggerNotificationForm()
    form.request = DummyRequest()
    form.on_request()
    assert form.notifications.choices == []
    assert not form.validate()

    form.request.app.principal.email_notification = True
    form.on_request()
    assert form.notifications.choices == [('email', 'Email')]
    assert 'email' in form.notifications.default

    form.request.app.principal.sms_notification = 'http://example.com'
    form.on_request()
    assert form.notifications.choices == [('email', 'Email'), ('sms', 'SMS')]
    assert 'email' in form.notifications.default
    assert 'sms' in form.notifications.default

    form.request.app.principal.webhooks = {'http://abc.com/1': None}
    form.on_request()
    assert form.notifications.choices == [
        ('email', 'Email'), ('sms', 'SMS'), ('webhooks', 'Webhooks')
    ]
    assert form.notifications.data == ['email', 'sms', 'webhooks']
    assert 'sms' in form.notifications.default
    assert 'webhooks' in form.notifications.default


def test_notifications_form(session):
    form = TriggerNotificationsForm()
    form.request = DummyRequest(session=session)
    form.on_request()
    assert form.notifications.choices == []
    assert form.elections.choices == []
    assert form.votes.choices == []
    assert form.latest_date(session) is None
    assert not form.validate()

    # Enable notification
    form.request.app.principal.email_notification = True
    form.request.app.principal.sms_notification = 'http://example.com'
    form.request.app.principal.webhooks = {'http://abc.com/1': None}

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
    session.flush()

    # Test on_request
    form.on_request()
    assert form.notifications.choices == [
        ('email', 'Email'), ('sms', 'SMS'), ('webhooks', 'Webhooks')
    ]
    assert form.notifications.data == ['email', 'sms', 'webhooks']
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
    assert form.vote_models(session) == []
    assert form.election_models(session) == []

    # Test submit
    form = TriggerNotificationsForm(
        DummyPostData({
            'notifications': ['email'],
            'votes': ['vote-3', 'vote-2'],
            'elections': ['majorz-election-2']
        })
    )
    form.request = DummyRequest(session=session)
    form.request.app.principal.email_notification = True
    form.on_request()
    assert form.validate()
    assert [vote.id for vote in form.vote_models(session)] == [
        'vote-3',
        'vote-2'
    ]
    assert [election.id for election in form.election_models(session)] == [
        'majorz-election-2',
    ]
