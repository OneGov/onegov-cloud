from onegov.election_day.forms import EmailSubscriptionForm
from onegov.election_day.forms import SmsSubscriptionForm
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest


def test_email_subscription_form():
    form = EmailSubscriptionForm()
    form.request = DummyRequest()
    form.on_request()
    assert not form.validate()

    form = EmailSubscriptionForm(DummyPostData({'email': 'test'}))
    form.request = DummyRequest()
    form.on_request()
    assert not form.validate()

    form = EmailSubscriptionForm(DummyPostData({'email': 'te@s.t'}))
    form.request = DummyRequest()
    form.on_request()
    assert form.validate()

    form = EmailSubscriptionForm(DummyPostData({
        'email': 'te@s.t',
        'domain': 'municipality',
        'domain_segment': 'a'
    }))
    form.request = DummyRequest()
    form.request.app.principal.segmented_notifications = True
    form.request.app.principal.get_entities = lambda x: ['a', 'b']
    form.on_request()
    assert form.domain_segment.choices == [('a', 'a'), ('b', 'b')]
    assert form.validate()


def test_sms_subscription_form():
    form = SmsSubscriptionForm()
    form.request = DummyRequest()
    form.on_request()
    assert not form.validate()

    form = SmsSubscriptionForm(DummyPostData({'phone_number': 'test'}))
    form.request = DummyRequest()
    form.on_request()
    assert not form.validate()

    form = SmsSubscriptionForm(DummyPostData({
        'phone_number': '+261339743405'
    }))
    form.request = DummyRequest()
    form.on_request()
    assert not form.validate()

    form = SmsSubscriptionForm(DummyPostData({
        'phone_number': '+41791234567'
    }))
    form.request = DummyRequest()
    form.on_request()
    assert form.validate()

    form = SmsSubscriptionForm(DummyPostData({
        'phone_number': '+41791234567',
        'domain': 'municipality',
        'domain_segment': 'a'
    }))
    form.request = DummyRequest()
    form.request.app.principal.segmented_notifications = True
    form.request.app.principal.get_entities = lambda x: ['a', 'b']
    form.on_request()
    assert form.domain_segment.choices == [('a', 'a'), ('b', 'b')]
    assert form.validate()
