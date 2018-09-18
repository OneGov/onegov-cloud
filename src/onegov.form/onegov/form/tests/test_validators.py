from onegov.form.validators import ValidPhoneNumber
from pytest import raises
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

    with raises(ValidationError):
        validator(None, Field(1234))
    with raises(ValidationError):
        validator(None, Field('1234'))

    with raises(ValidationError):
        validator(None, Field('+417911122333'))
    with raises(ValidationError):
        validator(None, Field('041791112233'))
    with raises(ValidationError):
        validator(None, Field('041791112233'))
    with raises(ValidationError):
        validator(None, Field('00791112233'))
