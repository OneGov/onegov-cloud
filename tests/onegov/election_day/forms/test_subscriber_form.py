from onegov.election_day.forms import EmailSubscriptionForm
from onegov.election_day.forms import SmsSubscriptionForm
from tests.onegov.election_day.common import DummyPostData


def test_email_subscription_form():
    form = EmailSubscriptionForm()
    assert not form.validate()

    form = EmailSubscriptionForm(DummyPostData({'email': 'test'}))
    assert not form.validate()

    form = EmailSubscriptionForm(DummyPostData({'email': 'te@s.t'}))
    assert form.validate()


def test_sms_subscription_form():
    form = SmsSubscriptionForm()
    assert not form.validate()

    form = SmsSubscriptionForm(DummyPostData({'phone_number': 'test'}))
    assert not form.validate()

    form = SmsSubscriptionForm(DummyPostData({
        'phone_number': '+261339743405'
    }))
    assert not form.validate()

    form = SmsSubscriptionForm(DummyPostData({
        'phone_number': '+41791234567'
    }))
    assert form.validate()
