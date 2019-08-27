from onegov.quill.validators import HtmlDataRequired
from pytest import raises
from wtforms.validators import ValidationError


def test_html_data_validator(session):

    class Field(object):
        def __init__(self, data):
            self.data = data

        def gettext(self, text):
            return text

    validator = HtmlDataRequired()

    validator(None, Field('Test'))
    validator(None, Field('<p>Test</p>'))

    with raises(ValidationError):
        validator(None, Field(None))
    with raises(ValidationError):
        validator(None, Field(''))
    with raises(ValidationError):
        validator(None, Field(' '))
    with raises(ValidationError):
        validator(None, Field('<p></p>'))
    with raises(ValidationError):
        validator(None, Field('<p> </p>'))
    with raises(ValidationError):
        validator(None, Field('<p><br></p>'))
    with raises(ValidationError):
        validator(None, Field('<br><br><br><br>'))
