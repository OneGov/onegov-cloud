import pytest

from onegov.election_day.forms.validators import ValidPhoneNumber
from onegov.election_day.forms.subscribe import SubscribeForm as SF
from wtforms.validators import ValidationError


def test_phone_number_validator():

    class Field(object):
        def __init__(self, data):
            self.data = data

    validator = ValidPhoneNumber()

    validator(None, Field(None))
    validator(None, Field(''))

    validator(None, Field('+41791112233'))
    validator(None, Field('0041791112233'))
    validator(None, Field('0791112233'))

    with pytest.raises(ValidationError):
        validator(None, Field(1234))
    with pytest.raises(ValidationError):
        validator(None, Field('1234'))

    with pytest.raises(ValidationError):
        validator(None, Field('+417911122333'))
    with pytest.raises(ValidationError):
        validator(None, Field('041791112233'))
    with pytest.raises(ValidationError):
        validator(None, Field('041791112233'))
    with pytest.raises(ValidationError):
        validator(None, Field('00791112233'))


def test_subscribe_form():
    assert SF().formatted_phone_number == None
    assert SF(phone_number='').formatted_phone_number == None
    assert SF(phone_number=123456).formatted_phone_number == None

    expected = '+41791112233'
    assert SF(phone_number='0791112233').formatted_phone_number == expected
    assert SF(phone_number='0041791112233').formatted_phone_number == expected
    assert SF(phone_number='+41791112233').formatted_phone_number == expected
