from onegov.election_day.forms import SmsSubscriptionForm


def test_sms_subscription_form():
    assert SmsSubscriptionForm().formatted_phone_number is None
    assert SmsSubscriptionForm(phone_number='').formatted_phone_number is None
    assert SmsSubscriptionForm(
        phone_number=123456
    ).formatted_phone_number is None

    for number in ('0791112233', '0041791112233', '+41791112233'):
        assert SmsSubscriptionForm(
            phone_number=number
        ).formatted_phone_number == '+41791112233'
