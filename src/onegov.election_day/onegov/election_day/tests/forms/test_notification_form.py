from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.tests import DummyRequest


def test_notification_form():
    form = TriggerNotificationForm()
    form.request = DummyRequest()
    form.on_request()
    assert form.notifications.choices == []
    assert not form.validate()

    form.request.app.principal.email_notification = True
    form.on_request()
    assert form.notifications.choices == [('email', 'Email')]
    assert form.notifications.data == ['email']

    form.request.app.principal.sms_notification = 'http://example.com'
    form.on_request()
    assert form.notifications.choices == [('email', 'Email'), ('sms', 'SMS')]
    assert form.notifications.data == ['email', 'sms']

    form.request.app.principal.webhooks = {'http://abc.com/1': None}
    form.on_request()
    assert form.notifications.choices == [
        ('email', 'Email'), ('sms', 'SMS'), ('webhooks', 'Webhooks')
    ]
    assert form.notifications.data == ['email', 'sms', 'webhooks']
